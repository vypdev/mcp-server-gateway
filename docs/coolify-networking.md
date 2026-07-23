# Coolify and Docker Networking

## Same Coolify host

If the gateway and a node run on the same Coolify host, attach them to a private Docker network. The gateway should address the node by its Compose service name, not a public DNS name.

```yaml
networks:
  mcp-private:
    driver: bridge

services:
  gateway:
    networks: [mcp-private]
  unifi-mcp:
    networks: [mcp-private]
```

Do not publish the node port to the host unless a separate operational requirement exists.

## Different hosts

Docker bridge networks are host-local. For nodes on `ai-core`, `NAS01`, or `Lab01`, use one of:

- private UniFi VLAN/routing;
- Tailscale or WireGuard;
- a private reverse proxy reachable only from the gateway;
- another authenticated private overlay.

Traffic should look like:

```text
Gateway → private address → node MCP endpoint
```

Not:

```text
Internet → node MCP endpoint
```

## Coolify requirements

Each application should define:

- explicit internal port;
- healthcheck endpoint;
- restart policy;
- read-only filesystem where compatible;
- dropped Linux capabilities;
- no Docker socket by default;
- secrets as runtime environment values;
- resource limits;
- structured logs.

## Initial rollout

1. Deploy gateway with no nodes enabled.
2. Deploy one read-only node in an isolated Coolify application.
3. Verify private connectivity from gateway to node.
4. Verify MCP initialize, tools/list, repeated calls, and timeout behavior.
5. Enable the node in the gateway registry.
6. Connect Hermes and OpenClaw read-only clients.
7. Add further nodes one at a time.
