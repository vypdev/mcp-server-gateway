# Architecture

## Primary model: one gateway per host

`mcp-server-gateway` is deployed on the server it manages. Hermes and OpenClaw connect to each remote instance as MCP clients.

```text
Hermes/OpenClaw on ai-core
       │ private authenticated MCP/HTTPS
       ├──────────────► MCP Gateway on NAS01
       ├──────────────► MCP Gateway on Lab01
       ├──────────────► MCP Gateway on another Coolify host
       └──────────────► future MCP Gateway on TrueNAS
```

There is no requirement for a central aggregator. A future aggregator could be added, but it is not part of the initial design.

## What a per-host gateway does

A gateway instance is a local control plane for its own host. It can expose typed tools for:

- host status and metrics;
- Docker container inventory and health;
- local Coolify application status;
- bounded service logs;
- named healthchecks;
- controlled deployments or restarts when explicitly enabled.

Hermes/OpenClaw do not receive the host's SSH private key, Docker credentials, or arbitrary shell access.

## Local adapters

The gateway may use host-local adapters internally:

```text
MCP Gateway on NAS01
  ├── Docker/Coolify adapter
  ├── host health adapter
  └── future TrueNAS adapter
```

Those adapters do not need to be separate MCP servers. They are implementation modules behind one host-local MCP endpoint.

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

## Host-local execution

For Coolify-managed applications, prefer the Coolify API or a narrowly scoped Docker adapter. Mounting `/var/run/docker.sock` into a gateway container grants near-root control of the host and must not be the default.

For systemd and host-level operations, use a small host agent or a privileged, explicitly reviewed adapter. A normal unprivileged container cannot safely control host systemd merely because it runs on the same machine.

## Transport

Use MCP Streamable HTTP over a private authenticated path. Avoid exposing legacy SSE-only endpoints publicly. Every host instance must support initialization, tools/list, repeated calls, bounded timeouts, and structured errors.
