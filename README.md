# MCP Server Gateway

A per-host MCP server for giving Hermes and OpenClaw controlled access to remote lab servers.

The gateway is deployed **on the server it manages**. It is not a central aggregator running on the current Hermes/OpenClaw host.

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

- `docs/architecture.md` — per-host deployment and trust boundaries.
- `docs/coolify-networking.md` — deploying the gateway inside each Coolify host.
- `docs/node-contract.md` — local host capability contract.
- `docs/security-model.md` — observer/operator/admin policy.
- `docs/profiles.md` — MCP profiles and Unix identity separation.
- `docs/operations.md` — rollout and verification checklist.
- `deploy/coolify/` — deployment guidance.

## Implementation status

The first executable slice is implemented:

- Streamable HTTP at `/mcp` with stateless sessions;
- `/healthz` and `/readyz`;
- fixed startup profiles `observer` and `operator`;
- host identity and resource status tools;
- Docker inventory tool when Docker is available to the runtime;
- operator-only `execute_command` using argv, no implicit shell;
- working-directory, timeout, argument-count, output-size, and environment limits;
- unprivileged container defaults for Coolify.

The current container executes commands inside its own runtime. Host-level command execution requires a deliberately deployed host adapter or host service account; mounting the host Docker socket or privileged host mounts is not enabled by default.

## Design rule

Every gateway instance must pass health, MCP initialization, tool listing, repeated calls, timeout handling, and audit checks from both Hermes and OpenClaw before it is trusted for that host.
