#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_URL="${GATEWAY_NODE_REPOSITORY_URL:-https://github.com/vypdev/gateway-node.git}"
REF="${GATEWAY_NODE_REF:-master}"

fail() {
  printf 'gateway-node installer: error: %s\n' "$*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Usage: install.sh [setup options]

Clones the repository into a temporary directory and delegates installation to
scripts/setup.sh. Setup options such as --profile, --bind, and --port are
forwarded unchanged.

Environment:
  GATEWAY_NODE_REF                 Git branch or tag (default: master)
  GATEWAY_NODE_REPOSITORY_URL      Git repository URL
EOF
  exit 0
fi

command -v git >/dev/null 2>&1 || fail "git is required"
[[ "$REF" =~ ^[A-Za-z0-9._/-]+$ ]] || fail "GATEWAY_NODE_REF contains unsupported characters"

checkout="$(mktemp -d "${TMPDIR:-/tmp}/gateway-node.XXXXXX")"
cleanup() {
  rm -rf "$checkout"
}
trap cleanup EXIT

printf 'gateway-node installer: cloning %s (%s)\n' "$REPOSITORY_URL" "$REF"
git clone --quiet --depth 1 --branch "$REF" "$REPOSITORY_URL" "$checkout/repository"

setup=("$checkout/repository/scripts/setup.sh")
[[ -x "${setup[0]}" ]] || fail "repository does not contain an executable scripts/setup.sh"

if [[ "$(id -u)" -eq 0 ]]; then
  "${setup[@]}" "$@"
else
  command -v sudo >/dev/null 2>&1 || fail "sudo is required when not running as root"
  sudo "${setup[@]}" "$@"
fi

printf 'gateway-node installer: complete\n'
