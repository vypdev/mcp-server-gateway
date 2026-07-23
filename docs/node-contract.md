# Node Contract

Every node registered with the gateway must provide a machine-readable declaration containing:

```yaml
id: unifi
endpoint: http://unifi-mcp:8000/mcp
transport: streamable-http
healthcheck: http://unifi-mcp:8000/healthz
capabilities:
  observer:
    - unifi_list_sites
    - unifi_list_devices
  operator: []
  admin: []
timeout_seconds: 15
max_response_bytes: 262144
```

## Required behavior

- Streamable HTTP MCP transport.
- `/healthz` and `/readyz` endpoints.
- Structured JSON errors.
- Bounded response size.
- Explicit timeout handling.
- No secrets in tool responses or logs.
- Stable tool names and schemas.
- Repeated calls must work without relying on a stale SSE session.

## Capability levels

`observer` is read-only. `operator` contains narrowly scoped reversible actions. `admin` is reserved for explicit infrastructure changes. An empty list means the capability is unavailable, not merely hidden from the model.

## Registration policy

The gateway must reject unknown node IDs, unknown tool names, public node endpoints, and capability escalation requested by a client.
