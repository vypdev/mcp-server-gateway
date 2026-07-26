#!/usr/bin/env bash
set -Eeuo pipefail

PROFILE="observer"
RECONFIGURE=0
INSTALL_DIR="/opt/mcp-server-gateway"
CONFIG_DIR="/etc/mcp-server-gateway"
STATE_DIR="/var/lib/mcp-server-gateway"
HOST_ID="$(hostname -s)"
BIND_HOST="127.0.0.1"
PORT="8000"
ALLOWED_CWDS=""

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
  printf 'setup: error: %s\n' "$*" >&2
  exit 1
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

[[ "$(id -u)" -eq 0 ]] || fail "run as root, for example: sudo ./scripts/setup.sh"
[[ "$(uname -s)" == "Linux" ]] || fail "native setup currently supports Linux only"
command -v systemctl >/dev/null || fail "systemd/systemctl is required"
command -v python3 >/dev/null || fail "python3 is required"

python3 - <<'PY' || exit 1
import sys
if sys.version_info < (3, 11):
    print("setup: error: Python 3.11 or newer is required", file=sys.stderr)
    raise SystemExit(1)
PY

case "$PROFILE" in
  observer) SERVICE_USER="mcp-observer" ;;
  operator) SERVICE_USER="mcp-operator" ;;
  *) fail "profile must be observer or operator" ;;
esac

[[ "$HOST_ID" =~ ^[A-Za-z0-9._-]+$ ]] || fail "host id contains unsupported characters"
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1 && PORT <= 65535 )) || fail "port must be between 1 and 65535"
[[ "$BIND_HOST" != *$'\n'* && "$BIND_HOST" != *$'\r'* ]] || fail "bind address contains a newline"
[[ "$ALLOWED_CWDS" != *$'\n'* && "$ALLOWED_CWDS" != *$'\r'* ]] || fail "allowed paths contain a newline"

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE="$REPO_ROOT/deploy/systemd/mcp-server-gateway.service"
[[ -f "$REPO_ROOT/pyproject.toml" ]] || fail "run this script from a repository checkout"
[[ -f "$TEMPLATE" ]] || fail "missing systemd service template: $TEMPLATE"

if ! id "$SERVICE_USER" >/dev/null 2>&1; then
  useradd --system --user-group --create-home \
    --home-dir "$STATE_DIR" --shell /usr/sbin/nologin "$SERVICE_USER"
  printf 'setup: created Unix user %s\n' "$SERVICE_USER"
else
  printf 'setup: using existing Unix user %s\n' "$SERVICE_USER"
fi

install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -d -o "$SERVICE_USER" -g "$SERVICE_USER" -m 0750 "$STATE_DIR"
install -d -o root -g root -m 0750 "$CONFIG_DIR"

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

CONFIG_FILE="$CONFIG_DIR/gateway.env"
tmp_unit=""
if [[ -e "$CONFIG_FILE" && "$RECONFIGURE" -ne 1 ]]; then
  current_profile="$(awk -F= '$1 == "MCP_PROFILE" {print $2; exit}' "$CONFIG_FILE" || true)"
  [[ "$current_profile" == "$PROFILE" ]] || fail "$CONFIG_FILE already exists with profile '$current_profile'; use --reconfigure only after reviewing it"
  printf 'setup: preserving existing %s\n' "$CONFIG_FILE"
else
  [[ "$RECONFIGURE" -eq 1 && -e "$CONFIG_FILE" ]] && cp -a "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)"
  [[ -n "$ALLOWED_CWDS" ]] || ALLOWED_CWDS="$STATE_DIR"
  tmp_config="$(mktemp)"
  trap 'rm -f "$tmp_config" "$tmp_unit"' EXIT
  printf '%s\n' \
    "MCP_HOST_ID=$HOST_ID" \
    "MCP_PROFILE=$PROFILE" \
    "MCP_ALLOWED_CWDS=$ALLOWED_CWDS" \
    "MCP_COMMAND_TIMEOUT_SECONDS=30" \
    "MCP_MAX_OUTPUT_BYTES=262144" \
    "MCP_MAX_COMMAND_ARGS=64" \
    "MCP_HOST=$BIND_HOST" \
    "MCP_PORT=$PORT" > "$tmp_config"
  install -o root -g root -m 0600 "$tmp_config" "$CONFIG_FILE"
fi

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
systemctl enable --now mcp-server-gateway.service

health_url="http://127.0.0.1:$PORT/healthz"
python3 - "$health_url" <<'PY'
import sys
import urllib.request
url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        if response.status != 200:
            raise SystemExit(f"setup: health check returned HTTP {response.status}")
except Exception as exc:
    raise SystemExit(f"setup: service started but health check failed: {exc}")
PY

printf 'setup: installed and started mcp-server-gateway\n'
printf 'setup: profile=%s user=%s endpoint=%s\n' "$PROFILE" "$SERVICE_USER" "$health_url"
printf 'setup: review %s before allowing remote access\n' "$CONFIG_FILE"
