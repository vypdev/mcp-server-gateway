# Runtime Profiles and Unix Identities

The gateway has two independent enforcement layers:

1. **MCP runtime profile** — which tools are registered and exposed.
2. **Unix identity** — which files, sockets, services, Docker APIs, and commands the process can actually access.

Both layers must agree. A profile is not a security boundary if its process can change its own configuration or restart itself with stronger privileges.

## Profiles

### Observer

```text
MCP_PROFILE=observer
Unix identity: mcp-observer
```

Exposes read-only tools:

- host status and metrics;
- process and service status;
- Docker inventory and bounded logs;
- Coolify application status;
- named healthchecks;
- read-only filesystem paths.

The observer identity must not:

- access operator configuration or secrets;
- write the gateway configuration;
- restart the gateway with another profile;
- access a write-capable Docker socket;
- use sudo to become the operator identity.

### Operator

```text
MCP_PROFILE=operator
Unix identity: mcp-operator
```

Exposes all observer tools plus explicitly enabled operator tools:

- restart allowlisted services or containers;
- trigger allowlisted Coolify deployments;
- execute commands according to the operator command policy;
- perform bounded maintenance operations.

The operator identity may use additional groups or narrowly scoped sudoers rules. It must still not be root by default.

## Profile selection

The profile is selected at deployment/startup time, not by an MCP tool call:

```env
MCP_PROFILE=observer
MCP_HOST_ID=lab01
```

Changing from observer to operator requires an external deployment or service-management action performed by an authorized administrator. The observer process must not be able to perform that transition.

## Recommended deployment shape

For high-risk hosts, run separate instances/endpoints:

```text
lab01-mcp-observer  → mcp-observer → read-only
lab01-mcp-operator  → mcp-operator → observer + approved writes
```

The operator endpoint should have stronger network restrictions and may require a separate client credential. A single operator instance is acceptable only when its endpoint, credentials, and host permissions are protected accordingly.

## Command execution

Operator command execution must use a policy, not an unrestricted model-controlled privilege escalation:

- execute as `mcp-operator`;
- validate working directory;
- filter environment variables;
- enforce timeout and output limits;
- record command, actor, host, exit code, and duration;
- redact secrets from audit output;
- require confirmation for disruptive operations;
- use argv execution by default, with shell mode explicitly enabled per host.

## Capability matrix

| Capability | Observer | Operator |
|---|---:|---:|
| Host status | yes | yes |
| Docker inventory | yes | yes |
| Service logs | yes | yes |
| Coolify status | yes | yes |
| Restart service | no | allowlist |
| Restart container | no | allowlist |
| Coolify deploy | no | allowlist + confirmation |
| Command execution | read-only named commands | policy-controlled |
| Arbitrary root shell | no | no |
