# Coolify and Docker Deployment

## Per-host deployment

Deploy one instance of `mcp-server-gateway` on every host that should be operated remotely:

```text
NAS01 → one gateway instance
Lab01  → one gateway instance
Other Coolify host → one gateway instance
TrueNAS → future instance
```

Each instance is configured for its own host and never assumes that Docker networking is shared with another server.

## Same-host Coolify access

If the gateway and Coolify applications run on the same host, the gateway may use a private Docker network to reach approved application endpoints by service name.

```yaml
networks:
  host-mcp-private:
    driver: bridge

services:
  mcp-gateway:
    networks: [host-mcp-private]
  approved-local-adapter:
    networks: [host-mcp-private]
```

Do not publish the adapter port publicly. Do not mount the Docker socket unless a later, explicit capability review approves it.

## Remote client access

Hermes/OpenClaw run on `ai-core` and connect to each host gateway over a private authenticated path:

- existing lab VLAN/routing;
- Tailscale or WireGuard;
- private reverse proxy;
- another authenticated overlay.

Docker bridge networks do not span hosts.

```text
Hermes/OpenClaw → private address of target host → local MCP gateway
```

Not:

```text
Internet → host Docker socket or unauthenticated MCP endpoint
```

## Coolify requirements per host

Each gateway application should define:

- explicit internal port;
- `/healthz` and `/readyz` checks;
- restart policy;
- read-only filesystem where compatible;
- dropped Linux capabilities;
- no Docker socket by default;
- secrets as host-local Coolify environment values;
- resource limits;
- structured logs.

## First rollout

1. Deploy one observer-only gateway on a non-critical Coolify host.
2. Verify that Hermes/OpenClaw can reach only that host's endpoint.
3. Verify MCP initialize, tools/list, repeated calls, and timeout behavior.
4. Test read-only Docker/Coolify inventory.
5. Add a second host instance only after the first passes the complete checklist.
6. Add operator actions per host, individually and explicitly.
