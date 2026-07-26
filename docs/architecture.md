# Architecture

## Primary model: one native gateway per host

`mcp-server-gateway` runs directly on the server it manages as a systemd service. Hermes and OpenClaw connect to each remote instance as MCP clients.

```text
MCP clients
       │ private authenticated MCP/HTTPS
       ├──────────────► Native MCP Gateway on a managed host
       ├──────────────► Native MCP Gateway on another managed host
       └──────────────► future Native MCP Gateway on another platform
```

There is no central aggregator and no requirement to run the gateway inside Coolify or Docker. Coolify and Docker are managed targets of each native gateway.

## What a per-host gateway does

A gateway instance is a local control plane for its own host. It can expose typed tools for:

- host status and metrics;
- Docker container inventory and health;
- local Coolify application status;
- bounded service logs;
- named healthchecks;
- controlled deployments or restarts when explicitly enabled;
- policy-controlled command execution as the gateway Unix user.

Hermes/OpenClaw do not receive the host's SSH private key, Docker credentials, or unrestricted root access.

## Local adapters

The native gateway may use host-local adapters internally:

```text
Native MCP Gateway on a managed host
  ├── Docker adapter
  ├── Coolify API adapter
  ├── host health adapter
  ├── systemd adapter
  └── command executor
```

These adapters do not need to be separate MCP servers. They are implementation modules behind one host-local MCP endpoint.

## Trust zones

```text
Zone A: agent clients
  Hermes / OpenClaw

Zone B: private transport
  authenticated network path to the target host

Zone C: per-host gateway
  authentication, authorization, audit, typed operations

Zone D: target host
  Docker, Coolify, services, systemd, storage
```

The gateway is the only component that crosses from Zone C into the target host. Clients do not bypass it.

## Native execution

The gateway process runs as a dedicated Unix identity, for example `mcp-operator`. Its effective capabilities come from that identity's UID/GID, supplementary groups, filesystem permissions, systemd sandboxing, and explicitly reviewed sudoers rules.

If Docker access is granted, treat membership in the `docker` group as root-equivalent. Prefer the Coolify API or narrowly scoped adapters where possible. Do not mount `/var/run/docker.sock` into a container as a shortcut.

## Transport

Use MCP Streamable HTTP over a private authenticated path. Avoid exposing legacy SSE-only endpoints publicly. Every host instance must support initialization, tools/list, repeated calls, bounded timeouts, and structured errors.
