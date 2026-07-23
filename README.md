# MCP Server Gateway

Architecture and deployment blueprint for a secure MCP gateway that connects Hermes and OpenClaw with infrastructure MCP nodes running in Coolify/Docker.

## Scope

The first target is Docker and Coolify-hosted nodes. TrueNAS integration is intentionally deferred until the Coolify path is stable.

```text
Hermes ───────┐
              ▼
        MCP Server Gateway
              │ private MCP network
      ┌───────┼────────┬─────────┐
      ▼       ▼        ▼         ▼
   UniFi    ai-core   NAS01     Lab01
    MCP      MCP       MCP       MCP
```

## Security defaults

- Observer/read-only capability is the default.
- Operator actions are separate, allowlisted, auditable, and confirmation-gated.
- Admin actions are disabled by default and require an explicit deployment profile.
- No arbitrary shell tool is exposed to agents.
- No Docker socket is exposed to the gateway by default.
- Secrets are provided by Coolify runtime variables or an approved secret manager, never Git.
- Node endpoints remain on private networking; the gateway is the only client-facing MCP endpoint.

## Repository layout

- `docs/architecture.md` — components, trust boundaries, and traffic flows.
- `docs/coolify-networking.md` — same-host Docker and cross-host networking.
- `docs/node-contract.md` — node registration and tool capability contract.
- `docs/security-model.md` — observer/operator/admin policy.
- `docs/operations.md` — rollout and verification checklist.
- `deploy/coolify/` — deployment templates and placeholders.

## Status

This repository currently contains the architecture and deployment contract. The executable gateway will be added after the node transport, authentication, and authorization contract has been reviewed.

## Design rule

A running container is not a verified integration. Every node must pass health, MCP initialization, tool listing, repeated calls, timeout handling, and audit checks from both Hermes and OpenClaw before it is enabled in production.
