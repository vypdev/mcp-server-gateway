#!/usr/bin/env bash
set -Eeuo pipefail

PROFILE="observer"
RECONFIGURE=0
INSTALL_DIR="/opt/mcp-server-gateway"
CONFIG_DIR="/etc/mcp-server-gateway"
STATE_DIR="/var/lib/mcp-server-gateway"
AUTH_FILE="$CONFIG_DIR/tokens.json"
AUTH_LOCK_FILE="$STATE_DIR/.tokens.json.lock"
MANAGED_USER_MARKER="$CONFIG_DIR/managed-user"
HOST_ID="$(hostname -s)"
BIND_HOST="127.0.0.1"
PORT="8000"
ALLOWED_CWDS=""

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  C_RESET=$'\033[0m'
  C_DIM=$'\033[2m'
  C_CYAN=$'\033[36m'
  C_GREEN=$'\033[32m'
  C_YELLOW=$'\033[33m'
  C_RED=$'\033[31m'
else
  C_RESET=""
  C_DIM=""
  C_CYAN=""
  C_GREEN=""
  C_YELLOW=""
  C_RED=""
fi
STEP=0
INSTALL_STARTED_AT=0

banner() {
  printf '\n%s╭────────────────────────────────────────────────────────────╮%s\n' "$C_CYAN" "$C_RESET"
  printf '%s│  MCP SERVER GATEWAY // NATIVE INSTALLER                  │%s\n' "$C_CYAN" "$C_RESET"
  printf '%s│  secure host-local control plane                          │%s\n' "$C_CYAN" "$C_RESET"
  printf '%s╰────────────────────────────────────────────────────────────╯%s\n\n' "$C_CYAN" "$C_RESET"
}

phase() {
  ((STEP += 1))
  printf '%s[%02d] %s%s\n' "$C_CYAN" "$STEP" "$1" "$C_RESET"
}

info() {
  printf '     %s•%s %s\n' "$C_DIM" "$C_RESET" "$1"
}

success() {
  printf '     %s✔%s %s\n' "$C_GREEN" "$C_RESET" "$1"
}

warning() {
  printf '     %s⚠%s %s\n' "$C_YELLOW" "$C_RESET" "$1"
}

probe_venv() {
  local probe_dir probe_log
  probe_dir="$(mktemp -d)"
  probe_log="$(mktemp)"
  if python3 -m venv "$probe_dir" >"$probe_log" 2>&1; then
    rm -rf "$probe_dir" "$probe_log"
    return 0
  fi
  VENV_ERROR="$(tr '\n' ' ' < "$probe_log")"
  rm -rf "$probe_dir" "$probe_log"
  return 1
}

usage() {
  cat <<'EOF'
Usage: sudo ./scripts/setup.sh [options]

Options:
  --profile observer|operator  Fixed MCP profile (default: observer)
  --host-id ID                 Stable host identity (default: hostname -s)
  --bind ADDRESS               Bind address (default: 127.0.0.1)
  --port PORT                  Listen port (default: 8000)
  --allowed-cwds PATHS         Colon-separated working-directory allowlist
  --reconfigure                Replace the generated environment file
  -h, --help                   Show this help
EOF
}

fail() {
  printf '%s✖ setup failed:%s %s\n' "$C_RED" "$C_RESET" "$*" >&2
  exit 1
}

APT_UPDATED=0
apt_update_once() {
  if (( APT_UPDATED == 0 )); then
    info "updating APT metadata"
    DEBIAN_FRONTEND=noninteractive apt-get update -qq || fail "apt-get update failed while preparing runtime dependencies"
    APT_UPDATED=1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      [[ $# -ge 2 ]] || fail "--profile requires a value"
      PROFILE="$2"
      shift 2
      ;;
    --host-id)
      [[ $# -ge 2 ]] || fail "--host-id requires a value"
      HOST_ID="$2"
      shift 2
      ;;
    --bind)
      [[ $# -ge 2 ]] || fail "--bind requires a value"
      BIND_HOST="$2"
      shift 2
      ;;
    --port)
      [[ $# -ge 2 ]] || fail "--port requires a value"
      PORT="$2"
      shift 2
      ;;
    --allowed-cwds)
      [[ $# -ge 2 ]] || fail "--allowed-cwds requires a value"
      ALLOWED_CWDS="$2"
      shift 2
      ;;
    --reconfigure)
      RECONFIGURE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown option: $1"
      ;;
  esac
done

banner
INSTALL_STARTED_AT="$SECONDS"
phase "Preflight host and runtime"
info "profile=$PROFILE | bind=$BIND_HOST | port=$PORT"
[[ "$(id -u)" -eq 0 ]] || fail "run as root, for example: sudo ./scripts/setup.sh"
[[ "$(uname -s)" == "Linux" ]] || fail "native setup currently supports Linux only"
command -v systemctl >/dev/null || fail "systemd/systemctl is required"

if ! command -v python3 >/dev/null 2>&1; then
  command -v apt-get >/dev/null 2>&1 || fail "python3 is missing and apt-get is not available"
  warning "python3 is missing; installing the system runtime"
  apt_update_once
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3 || fail "could not install python3"
  success "python3 installed"
fi
command -v python3 >/dev/null || fail "python3 is required"

python3 - <<'PY' || exit 1
import sys
if sys.version_info < (3, 11):
    print("setup: error: Python 3.11 or newer is required", file=sys.stderr)
    raise SystemExit(1)
PY

if ! probe_venv; then
  venv_package="$(python3 -c 'import sys; print(f"python{sys.version_info.major}.{sys.version_info.minor}-venv")')"
  if command -v apt-get >/dev/null 2>&1; then
    warning "Python venv support is missing; installing $venv_package"
    apt_update_once
    if ! apt-cache show "$venv_package" >/dev/null 2>&1; then
      warning "$venv_package is not available; falling back to python3-venv"
      venv_package="python3-venv"
    fi
    info "installing $venv_package"
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$venv_package" || fail "could not install $venv_package (details: $VENV_ERROR)"
    probe_venv || fail "Python venv support is still unavailable after installing $venv_package (details: $VENV_ERROR)"
    success "Python venv support installed"
  else
    fail "Python venv support is unavailable and apt-get is not present (install the matching pythonX.Y-venv package; details: $VENV_ERROR)"
  fi
else
  success "Python venv support ready"
fi

case "$PROFILE" in
  observer) SERVICE_USER="mcp-observer" ;;
  operator) SERVICE_USER="mcp-operator" ;;
  *) fail "profile must be observer or operator" ;;
esac

phase "Validate installation contract"
info "service identity=$SERVICE_USER"
info "installation root=$INSTALL_DIR"
info "state root=$STATE_DIR"

[[ "$HOST_ID" =~ ^[A-Za-z0-9._-]+$ ]] || fail "host id contains unsupported characters"
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1 && PORT <= 65535 )) || fail "port must be between 1 and 65535"
[[ "$BIND_HOST" != *$'\n'* && "$BIND_HOST" != *$'\r'* ]] || fail "bind address contains a newline"
[[ "$ALLOWED_CWDS" != *$'\n'* && "$ALLOWED_CWDS" != *$'\r'* ]] || fail "allowed paths contain a newline"

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$REPO_ROOT/deploy/systemd/mcp-server-gateway.service"
[[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "run this script from a repository checkout"
[[ -f "$TEMPLATE" ]] || fail "missing systemd service template: $TEMPLATE"
success "repository and systemd template verified"

phase "Provision least-privilege service identity"
if [[ -r "$MANAGED_USER_MARKER" ]] \
  && [[ "$(awk -F= '$1 == "MCP_SERVICE_USER" {print $2; exit}' "$MANAGED_USER_MARKER")" == "$SERVICE_USER" ]] \
  && [[ "$(awk -F= '$1 == "MCP_SERVICE_USER_CREATED" {print $2; exit}' "$MANAGED_USER_MARKER")" == "1" ]]; then
  USER_CREATED=1
fi
if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --user-group --create-home \
    --home-dir "$STATE_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
  USER_CREATED=1
  success "created Unix user $SERVICE_USER"
else
  info "using existing Unix user $SERVICE_USER"
fi

phase "Build isolated gateway runtime"
install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$STATE_DIR"
install -d -o root -g "$SERVICE_USER" -m 0750 "$CONFIG_DIR"

tar -C "$REPO_ROOT" \
  --exclude=.git --exclude=.venv --exclude=__pycache__ \
  --exclude='*.pyc' -cf - . | tar -C "$INSTALL_DIR" -xf -
chown -R root:root "$INSTALL_DIR"
chmod -R a=rX "$INSTALL_DIR"

if [[ ! -x "$INSTALL_DIR/.venv/bin/python" ]]; then
  python3 -m venv "$INSTALL_DIR/.venv"
fi
"$INSTALL_DIR/.venv/bin/pip" install --quiet --upgrade "$INSTALL_DIR"
chown -R root:root "$INSTALL_DIR/.venv"
chmod -R a=rX "$INSTALL_DIR/.venv"
success "isolated Python runtime ready"

phase "Install operator CLI"
CLI_TARGET="$INSTALL_DIR/.venv/bin/mcp-gateway"
CLI_PATH="/usr/local/bin/mcp-gateway"
[[ -x "$CLI_TARGET" ]] || fail "mcp-gateway CLI was not installed: $CLI_TARGET"
if [[ -e "$CLI_PATH" || -L "$CLI_PATH" ]]; then
  [[ -L "$CLI_PATH" && "$(readlink "$CLI_PATH")" == "$CLI_TARGET" ]] || fail "$CLI_PATH already exists and is not managed by this installation"
else
  ln -s "$CLI_TARGET" "$CLI_PATH"
fi
success "CLI linked at $CLI_PATH"

phase "Render protected configuration"
CONFIG_FILE="$CONFIG_DIR/gateway.env"
tmp_config=""
tmp_unit=""
tmp_marker=""
if [[ -e "$CONFIG_FILE" && "$RECONFIGURE" -ne 1 ]]; then
  current_profile="$(awk -F= '$1 == "MCP_PROFILE" {print $2; exit}' "$CONFIG_FILE" || true)"
  [[ "$current_profile" == "$PROFILE" ]] || fail "$CONFIG_FILE already exists with profile '$current_profile'; use --reconfigure only after reviewing it"
  configured_port="$(awk -F= '$1 == "MCP_PORT" {print $2; exit}' "$CONFIG_FILE" || true)"
  [[ "$configured_port" =~ ^[0-9]+$ ]] && (( configured_port >= 1 && configured_port <= 65535 )) || fail "$CONFIG_FILE contains an invalid MCP_PORT"
  PORT="$configured_port"
  configured_bind="$(awk -F= '$1 == "MCP_HOST" {print $2; exit}' "$CONFIG_FILE" || true)"
  [[ -n "$configured_bind" ]] || fail "$CONFIG_FILE must define MCP_HOST"
  BIND_HOST="$configured_bind"
  configured_auth_file="$(awk -F= '$1 == "MCP_AUTH_FILE" {print $2; exit}' "$CONFIG_FILE" || true)"
  [[ -n "$configured_auth_file" ]] || fail "$CONFIG_FILE predates authentication; rerun with --reconfigure after reviewing the generated backup"
  AUTH_FILE="$configured_auth_file"
  AUTH_LOCK_FILE="$STATE_DIR/.tokens.json.lock"
  printf 'setup: preserving existing %s and its effective endpoint\n' "$CONFIG_FILE"
else
  [[ "$RECONFIGURE" -eq 1 && -e "$CONFIG_FILE" ]] && cp -a "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"
  [[ -n "$ALLOWED_CWDS" ]] || ALLOWED_CWDS="$STATE_DIR"
  tmp_config="$(mktemp)"
  trap 'rm -f "$tmp_config" "$tmp_unit" "$tmp_marker"' EXIT
  printf '%s\n' \
    "MCP_HOST_ID=$HOST_ID" \
    "MCP_PROFILE=$PROFILE" \
    "MCP_ALLOWED_CWDS=$ALLOWED_CWDS" \
    "MCP_COMMAND_TIMEOUT_SECONDS=30" \
    "MCP_MAX_OUTPUT_BYTES=262144" \
    "MCP_MAX_COMMAND_ARGS=64" \
    "MCP_HOST=$BIND_HOST" \
    "MCP_PORT=$PORT" \
    "MCP_AUTH_FILE=$AUTH_FILE" \
    "MCP_AUTH_LOCK_FILE=$AUTH_LOCK_FILE" > "$tmp_config"
  install -o root -g root -m 0600 "$tmp_config" "$CONFIG_FILE"
fi
[[ "$AUTH_FILE" == "$CONFIG_DIR/"* ]] || fail "MCP_AUTH_FILE must remain inside $CONFIG_DIR"

trap 'rm -f "$tmp_config" "$tmp_unit" "$tmp_marker"' EXIT
tmp_marker="$(mktemp)"
printf '%s\n' \
  "MCP_SERVICE_USER=$SERVICE_USER" \
  "MCP_SERVICE_USER_CREATED=$USER_CREATED" > "$tmp_marker"
install -o root -g root -m 0600 "$tmp_marker" "$MANAGED_USER_MARKER"
rm -f "$tmp_marker"
tmp_marker=""
success "configuration and service identity marker secured"

phase "Provision client authentication"
if [[ ! -e "$AUTH_FILE" ]]; then
  install -o root -g "$SERVICE_USER" -m 0640 /dev/null "$AUTH_FILE"
  printf '%s\n' '{"version":1,"tokens":[]}' > "$AUTH_FILE"
  chown root:"$SERVICE_USER" "$AUTH_FILE"
else
  chown root:"$SERVICE_USER" "$AUTH_FILE"
  chmod 0640 "$AUTH_FILE"
fi
if [[ ! -e "$AUTH_LOCK_FILE" ]]; then
  install -o root -g "$SERVICE_USER" -m 0660 /dev/null "$AUTH_LOCK_FILE"
else
  chown root:"$SERVICE_USER" "$AUTH_LOCK_FILE"
  chmod 0660 "$AUTH_LOCK_FILE"
fi
token_count="$($INSTALL_DIR/.venv/bin/python -c 'import json, sys; print(len(json.load(open(sys.argv[1], encoding="utf-8"))["tokens"]))' "$AUTH_FILE")" \
  || fail "invalid token store: $AUTH_FILE"
if [[ "$token_count" == "0" ]]; then
  bootstrap_credentials="$($CLI_TARGET authenticate bootstrap)" || fail "could not create bootstrap authentication token"
  printf '%s\n' "$bootstrap_credentials"
else
  info "preserving existing client tokens ($token_count active)"
fi

phase "Register and activate systemd service"

escape_sed() {
  printf '%s' "$1" | sed 's/[&|]/\\&/g'
}
tmp_unit="$(mktemp)"
sed \
  -e "s|@MCP_USER@|$(escape_sed "$SERVICE_USER")|g" \
  -e "s|@INSTALL_DIR@|$(escape_sed "$INSTALL_DIR")|g" \
  -e "s|@CONFIG_FILE@|$(escape_sed "$CONFIG_FILE")|g" \
  -e "s|@STATE_DIR@|$(escape_sed "$STATE_DIR")|g" \
  "$TEMPLATE" > "$tmp_unit"
install -o root -g root -m 0644 "$tmp_unit" /etc/systemd/system/mcp-server-gateway.service
rm -f "$tmp_unit"
trap - EXIT

systemctl daemon-reload
systemctl enable mcp-server-gateway.service
systemctl restart mcp-server-gateway.service
success "systemd enabled and service restarted"

phase "Verify live health endpoint"
case "$BIND_HOST" in
  0.0.0.0|"") health_host="127.0.0.1" ;;
  ::|"::0") health_host="[::1]" ;;
  *:*) health_host="[$BIND_HOST]" ;;
  *) health_host="$BIND_HOST" ;;
esac
health_url="http://$health_host:$PORT/healthz"
python3 - "$health_url" <<'PY'
import sys
import time
import urllib.request
url = sys.argv[1]
last_error = None
for _ in range(15):
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status}")
            break
    except Exception as exc:
        last_error = exc
        time.sleep(1)
else:
    raise SystemExit(f"setup: service started but health check failed after retries: {last_error}")
PY
success "health check passed at $health_url"

elapsed_seconds=$((SECONDS - INSTALL_STARTED_AT))
printf '\n%s╭────────────────────────────────────────────────────────────╮%s\n' "$C_GREEN" "$C_RESET"
printf '%s│  INSTALLATION COMPLETE                                     │%s\n' "$C_GREEN" "$C_RESET"
printf '%s╰────────────────────────────────────────────────────────────╯%s\n' "$C_GREEN" "$C_RESET"
success "profile=$PROFILE | user=$SERVICE_USER | elapsed=${elapsed_seconds}s"
success "CLI: $CLI_PATH"
info "review $CONFIG_FILE before allowing remote access"
