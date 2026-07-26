# MCP Server Gateway

A native, per-host MCP server that gives MCP clients controlled access to the operating system on which it runs.

```text
MCP clients
    │ private authenticated transport
    ▼
Native MCP Server Gateway
    │
    ├── host identity and status
    ├── bounded process execution
    ├── service-specific adapters
    └── filesystem paths explicitly allowed by policy
```

The gateway is not a central aggregator. Each installation is a local authority for exactly one host and runs as a system service under a dedicated Unix identity.

## Quick install

For the shortest installation path, review `install.sh` and run it through Bash from the selected repository branch:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/vypdev/mcp-server-gateway/master/install.sh)"
```

The bootstrap clones the repository into a temporary directory, invokes `scripts/setup.sh`, and removes the temporary checkout. Pass setup options after `--` when invoking Bash explicitly:

```bash
curl -fsSL https://raw.githubusercontent.com/vypdev/mcp-server-gateway/master/install.sh \
  | /bin/bash -s -- --profile operator
```

The clone-and-run path remains available for users who want to inspect the repository first.

## Clone and setup

On a Linux host with systemd:

```bash
git clone --branch master --depth 1 \
  https://github.com/vypdev/mcp-server-gateway.git
cd mcp-server-gateway
sudo ./scripts/setup.sh --profile observer
```

Use the operator profile only after reviewing the service identity and its permissions:

```bash
sudo ./scripts/setup.sh --profile operator
```

The setup script creates the matching `mcp-observer` or `mcp-operator` account when missing, installs a virtual environment and systemd unit, preserves existing configuration, and starts the service.

## Security defaults

- Observer/read-only capability is the default.
- Operator command execution is exposed only in the operator profile.
- The profile is fixed for the process lifetime.
- The service runs as a dedicated non-root Unix identity.
- Commands use argv execution with no implicit shell.
- Working directories, timeouts, argument count, environment, and output are bounded.
- The service binds to loopback by default.
- The MCP endpoint must remain on a private authenticated network.
- Secrets are never stored in Git or returned in tool output.

## Architecture

```text
src/mcp_gateway/
├── domain/
│   ├── commands.py       # immutable command value objects
│   └── profiles.py       # profile rules
├── application/
│   ├── ports.py          # infrastructure interfaces
│   └── services.py       # use cases
├── infrastructure/
│   ├── settings.py       # environment configuration
│   ├── subprocess_runner.py
│   └── host_info.py
├── presentation/
│   └── mcp_server.py     # MCP and HTTP adapter
└── main.py               # composition root
```

Dependency direction is inward:

```text
presentation → application → domain
infrastructure → application/domain
main composes all layers
```

The domain and application layers do not import MCP, Starlette, psutil, subprocess, systemd, or any vendor-specific integration.

## Profiles

```text
observer:
  host_get_identity
  host_get_status

operator:
  observer tools
  execute_command
```

The operator profile does not mean root. The effective capability is the intersection of the MCP profile and the Unix identity used by the service.

## Service management

The installer enables the service for automatic startup at boot and configures restart after unexpected failures. After installation, use the global CLI:

```bash
mcp-gateway doctor
mcp-gateway status
sudo mcp-gateway start
sudo mcp-gateway restart
sudo mcp-gateway stop
sudo mcp-gateway uninstall --yes
```

`start` and `stop` are idempotent: they report when the requested state is already active. `doctor` checks the unit, configuration, Unix identity, installed executable, service state, and health endpoint without printing secret values. `uninstall` stops and disables the unit, then removes the managed service unit, installation directory, configuration, state, and CLI symlink. It is interactive by default and requires typing `UNINSTALL`; `--yes` is required in non-interactive automation. A Unix service account is removed only when the installer created and marked that account; pre-existing accounts are preserved.

## Implementation status

Implemented and tested:

- Streamable HTTP MCP transport at `/mcp`;
- `/healthz` and `/readyz`;
- fixed `observer` and `operator` profiles;
- host identity and resource status tools;
- bounded operator command execution;
- native systemd installation;
- one-line bootstrap installer;
- `mcp-gateway` lifecycle and diagnostics CLI;
- automated tests and CI.

## Documentation

- `docs/architecture.md` — layers and trust boundaries.
- `docs/native-deployment.md` — generic systemd installation.
- `docs/node-contract.md` — host identity and MCP contract.
- `docs/security-model.md` — profile and capability policy.
- `docs/profiles.md` — profile and Unix identity separation.
- `docs/operations.md` — rollout and verification.
- `deploy/systemd/` — service template.

Every installation must pass health, initialization, tool listing, repeated calls, timeout handling, and client validation before it is trusted.
