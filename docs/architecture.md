# Architecture

## Primary model: one native gateway per host

The gateway runs directly on the operating system it manages as a systemd service. Clients connect to each installation as an MCP server.

```text
MCP clients
       │ private authenticated MCP transport
       ├──────────────► Native MCP Gateway on a managed host
       ├──────────────► Native MCP Gateway on another managed host
       └──────────────► Future Native MCP Gateway on another platform
```

There is no central aggregator. Each installation is a local authority for exactly one host.

## Layers

```text
Presentation
  MCP/HTTP adapter
        │
Application
  use cases and ports
        │
Domain
  profiles, command values, invariants
        ▲
Infrastructure
  operating-system adapters
```

Dependency direction points inward. Domain and application code remain independent of the transport framework and operating-system libraries.

## Host-local adapters

The native gateway may expose carefully reviewed adapters for:

- host identity and resource status;
- process execution;
- service status and logs;
- health checks;
- filesystem operations;
- future host-specific integrations.

Adapters are implementation modules behind one host-local MCP endpoint. They are not separate MCP servers.

## Trust zones

```text
Zone A: MCP clients
Zone B: private authenticated transport
Zone C: gateway authentication, authorization, audit, and typed operations
Zone D: operating-system resources
```

Clients do not bypass the gateway. The gateway is the only component that crosses from the client transport into host resources.

## Native execution

The service runs as a dedicated Unix identity. Effective capabilities come from that identity's UID/GID, supplementary groups, filesystem permissions, service sandboxing, and explicitly reviewed privilege rules.

The MCP profile alone never grants operating-system privileges.

## Transport

Use Streamable HTTP over a private authenticated path. Every installation must support initialization, tool listing, repeated calls, bounded timeouts, and structured errors.
