# Host Gateway Contract

Every target server runs one gateway instance with a host-specific identity and policy.

```yaml
id: managed-host
host: managed-host
endpoint: https://gateway.<private-domain>/mcp
transport: streamable-http
capabilities:
  observer:
    - host_get_status
    - docker_list_containers
    - coolify_list_applications
  operator: []
  admin: []
timeout_seconds: 15
max_response_bytes: 262144
```

The `id` identifies the target host, not a central node. Hermes and OpenClaw select the gateway instance according to the task.

## Required behavior

- Streamable HTTP MCP transport.
- `/healthz` and `/readyz` endpoints.
- Host-scoped authorization.
- Structured JSON errors.
- Bounded response size.
- Explicit timeout handling.
- No secrets in tool responses or logs.
- Stable typed tool names and schemas.
- Repeated calls work without a stale SSE session.
- The gateway cannot silently operate on a different host than its identity.

## Capability levels

`observer` is read-only. `operator` contains narrowly scoped reversible actions. `admin` is reserved for explicit host changes. An empty list means the capability is unavailable.

## Registration policy

The client configuration must map each endpoint to one host identity. The gateway must reject unknown tool names, capability escalation, and requests that target another host through a host-local instance.
