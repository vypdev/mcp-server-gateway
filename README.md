# MCP Server Gateway

A per-host MCP server for giving Hermes and OpenClaw controlled access to remote lab servers.

The gateway is deployed **natively on the server it manages** as a systemd service. It is not a central aggregator and it is not deployed inside Coolify or Docker for the host-control use case.

```text
Hermes/OpenClaw on ai-core
        │
        ├── MCP Server Gateway on NAS01
        ├── MCP Server Gateway on Lab01
        ├── MCP Server Gateway on another lab host
        └── future MCP Server Gateway on TrueNAS
```

Each instance is a local authority for one host. It can inspect and operate that host's Docker/Coolify services without giving Hermes or OpenClaw direct SSH access, shell access, or Docker credentials.

## Scope

The first target is Coolify/Docker hosts. TrueNAS is intentionally deferred until the per-host deployment path is stable.

## Security defaults

- Observer/read-only capability is the default.
- Operator actions are separate, allowlisted, auditable, and confirmation-gated.
- Admin actions are disabled by default.
- No arbitrary shell tool is exposed to agents.
- Docker socket access is not enabled by default; if required, use a restricted socket proxy or local adapter.
- Secrets are provided by the target host's Coolify runtime variables or an approved secret manager, never Git.
- The MCP endpoint is private and authenticated.

## Repository layout

- `docs/architecture.md` — native per-host deployment and trust boundaries.
- `docs/native-deployment.md` — systemd installation and Lab01 rollout.
- `docs/coolify-networking.md` — legacy/reference networking notes; Coolify is managed by the gateway, not its runtime.
- `docs/node-contract.md` — local host capability contract.
- `docs/security-model.md` — observer/operator/admin policy.
- `docs/profiles.md` — MCP profiles and Unix identity separation.
- `docs/operations.md` — rollout and verification checklist.
- `deploy/systemd/` — native service templates.
- `deploy/coolify/` — retained as a deprecated reference only.

## Implementation status

The first executable slice is implemented:

- Streamable HTTP at `/mcp` with stateless sessions;
- `/healthz` and `/readyz`;
- fixed startup profiles `observer` and `operator`;
- host identity and resource status tools;
- Docker inventory tool when Docker is available to the runtime;
- operator-only `execute_command` using argv, no implicit shell;
- native systemd deployment templates for the host-control runtime;
- a Docker image retained only for isolated development/tests, not as the Lab01 deployment model.

The native service executes as its configured Unix identity on the managed host. The effective capabilities therefore come from that user's UID/GID, groups, filesystem permissions, systemd policy, and any explicitly reviewed sudoers rules.

The Lab01 deployment must use the native systemd path described in `docs/native-deployment.md`. Coolify remains a managed target of the gateway, not the runtime for the gateway itself.

## Design rule

Every gateway instance must pass health, MCP initialization, tool listing, repeated calls, timeout handling, and audit checks from both Hermes and OpenClaw before it is trusted for that host.
