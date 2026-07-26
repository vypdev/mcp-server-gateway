# Security Policy

## Runtime profiles

Each host runs one gateway instance with a fixed startup profile:

- `observer`: read-only tools and gateway-owned diagnostics.
- `operator`: observer capabilities plus policy-controlled command execution and approved operations.

An MCP client cannot change the profile. Profile changes require an external systemd/service deployment action performed by an authorized administrator.

## Command execution

`execute_command` uses `argv` with `shell=False`, runs as the gateway Unix identity, and enforces working-directory, timeout, argument-count, output-size, and environment limits. Shell mode and host-level privileged access are not enabled by default.

## Deployment

The supported production runtime is a native systemd service on the managed host, with a dedicated Unix identity and no root execution by default. Container files are retained only for isolated development/tests; they are not the production deployment model.

Never commit credentials, tokens, SSH keys, Docker socket exports, or Coolify environment files.
