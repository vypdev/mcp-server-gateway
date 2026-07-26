# Security Policy

## Runtime profiles

Each host runs one gateway instance with one fixed startup profile:

- `observer`: read-only host information.
- `operator`: observer capabilities plus policy-controlled command execution.

An MCP client cannot change the profile. Profile changes require an external system service action performed by an authorized administrator.

## Command execution

`execute_command` uses argv with `shell=False`, runs as the service Unix identity, and enforces working-directory, timeout, argument-count, output-size, and environment limits.

The service is not root by default. Additional groups or privilege rules must be reviewed as host-specific policy and must not be assumed by the application.

## Deployment

The supported production runtime is a native systemd service on the managed host. The setup script creates only the dedicated Unix identity, application environment, state directory, and service unit. It does not grant additional host privileges or change network policy.

Keep the MCP endpoint on a private authenticated transport. Never commit credentials, tokens, SSH keys, private certificates, or environment files.
