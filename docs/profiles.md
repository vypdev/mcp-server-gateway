# Runtime Profiles and Unix Identities

The gateway has two independent enforcement layers:

1. **MCP runtime profile** — which tools are registered and exposed.
2. **Unix identity** — which files, sockets, services, and processes the service can actually access.

Both layers must agree. A profile is not a security boundary if its process can change its own configuration or restart itself with stronger privileges.

## Observer

```text
MCP_PROFILE=observer
Unix identity: mcp-observer
```

Exposes read-only host information and diagnostics.

The observer identity must not:

- access operator configuration;
- write gateway configuration;
- restart the gateway with another profile;
- use privilege escalation to become the operator identity.

## Operator

```text
MCP_PROFILE=operator
Unix identity: mcp-operator
```

Exposes all observer tools plus policy-controlled command execution.

The operator identity may use additional groups or narrowly scoped privilege rules. It must not be root by default.

## Profile selection

The profile is selected at deployment/startup time, not by an MCP tool call:

```env
MCP_PROFILE=observer
MCP_HOST_ID=managed-host
```

Changing from observer to operator requires an external service-management action performed by an authorized administrator.

## Deployment shape

Run one gateway instance per host and keep its profile fixed for the process lifetime:

```text
managed-host-gateway → mcp-observer  → read-only
managed-host-gateway → mcp-operator  → observer + command policy
```

The operator profile includes observer capabilities. The observer profile cannot activate operator capabilities or restart itself with stronger privileges.

## Command execution

Operator command execution must use a policy:

- execute as the service Unix identity;
- validate working directory;
- filter environment variables;
- enforce timeout and output limits;
- record command, actor, host, exit code, and duration;
- redact secrets from audit output;
- require confirmation for disruptive operations;
- use argv execution by default.

## Capability matrix

| Capability | Observer | Operator |
|---|---:|---:|
| Host identity | yes | yes |
| Host status | yes | yes |
| Read-only diagnostics | yes | yes |
| Command execution | no | policy-controlled |
| Privilege escalation | no | no by default |
