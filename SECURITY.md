# Security Policy

## Runtime profiles

Each host runs one gateway instance with a fixed startup profile:

- `observer`: read-only tools and gateway-owned diagnostics.
- `operator`: observer capabilities plus policy-controlled command execution and approved operations.

An MCP client cannot change the profile. Profile changes require an external Coolify/service deployment action.

## Command execution

`execute_command` uses `argv` with `shell=False`, runs as the gateway Unix identity, and enforces working-directory, timeout, argument-count, output-size, and environment limits. Shell mode and host-level privileged access are not enabled by default.

## Deployment

The default image is unprivileged, drops Linux capabilities, uses a read-only filesystem, and does not mount the Docker socket. Add host adapters or Docker access only through an explicit host-specific review.

Never commit credentials, tokens, SSH keys, Docker socket exports, or Coolify environment files.
