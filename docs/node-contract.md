# Host Gateway Contract

Every target server runs one gateway instance with a host-specific identity and policy.

```yaml
id: managed-host
host: managed-host
endpoint: https://gateway.<private-domain>/mcp
transport: streamable-http
capabilities:
  observer:
    - host_get_identity
    - host_get_status
  operator:
    - execute_command
timeout_seconds: 30
max_response_bytes: 262144
```

The identity identifies the target host. Clients select the gateway instance according to the task.

## Required behavior

- Streamable HTTP MCP transport.
- `/healthz` and `/readyz` endpoints.
- Host-scoped authorization.
- Structured JSON errors.
- Bounded response size.
- Explicit timeout handling.
- No secrets in tool responses or logs.
- Stable typed tool names and schemas.
- Repeated calls work without stale sessions.
- The gateway cannot silently operate on a different host than its identity.

## Capability levels

`observer` is read-only. `operator` adds policy-controlled command execution. An empty capability means unavailable.

## Registration policy

Client configuration maps each endpoint to one host identity. The gateway rejects unknown tools, capability escalation, and requests that target another host through a host-local instance.
