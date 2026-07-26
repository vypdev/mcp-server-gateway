#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_URL="${MCP_GATEWAY_REPOSITORY_URL:-https://github.com/vypdev/mcp-server-gateway.git}"
REF="${MCP_GATEWAY_REF:-master}"

fail() {
  printf 'mcp-gateway installer: error: %s\n' "$*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: install.sh [setup options]

Clones the repository into a temporary directory and delegates installation to
scripts/setup.sh. Setup options such as --profile, --bind, and --port are
forwarded unchanged.

Environment:
  MCP_GATEWAY_REF                 Git branch or tag (default: master)
  MCP_GATEWAY_REPOSITORY_URL      Git repository URL
EOF
  exit 0
fi

command -v git >/dev/null 2>&1 || fail "git is required"
[[ "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || fail "MCP_GATEWAY_REF contains unsupported characters"

checkout="$(mktemp -d "${TMPDIR:-/tmp}/mcp-gateway.XXXXXX")"
cleanup() {
  rm -rf "$checkout"
}
trap cleanup EXIT

printf 'mcp-gateway installer: cloning %s (%s)\n' "$REPOSITORY_URL" "$REF"
git clone --quiet --depth 1 --branch "$REF" "$REPOSITORY_URL" "$checkout/repository"

setup=("$checkout/repository/scripts/setup.sh")
[[ -x "${setup[0]}" ]] || fail "repository does not contain an executable scripts/setup.sh"

if [[ "$(id -u)" -eq 0 ]]; then
  "${setup[@]}" "$@"
else
  command -v sudo >/dev/null 2>&1 || fail "sudo is required when not running as root"
  sudo "${setup[@]}" "$@"
fi

printf 'mcp-gateway installer: complete\n'
