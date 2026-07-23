# Architecture

## Components

### Client agents

Hermes and OpenClaw connect only to the gateway MCP endpoint. They do not receive Docker credentials, SSH private keys, UniFi credentials, or arbitrary host access.

### Gateway

The gateway is the policy enforcement point. It should:

- authenticate clients;
- expose only registered node tools;
- apply capability policy per client/agent;
- route requests to nodes;
- enforce timeouts and response limits;
- attach correlation IDs;
- record audit events without secrets;
- return structured errors;
- prevent cross-node credential leakage.

### Nodes

A node is a small MCP server close to the system it observes or controls. Examples:

- `unifi-mcp` — UniFi inventory and health;
- `host-mcp` — read-only host, Docker, systemd, and logs;
- `coolify-mcp` — applications and deployments;
- future `truenas-mcp` — TrueNAS storage and services.

Nodes should not expose arbitrary shell execution. They should publish typed tools with explicit input schemas.

## Trust zones

```text
Zone A: agent clients
  Hermes / OpenClaw

Zone B: gateway
  authentication, routing, authorization, audit

Zone C: node network
  Coolify services and private node endpoints

Zone D: infrastructure
  UniFi, Docker, systemd, storage, controllers
```

The gateway may connect to Zone C, but clients must not bypass it to reach Zone D.

## Request flow

```text
1. Hermes/OpenClaw authenticates to gateway.
2. Gateway maps client identity to capability profile.
3. Gateway validates node and tool allowlists.
4. Gateway forwards a typed MCP request to one node.
5. Node validates its own local policy and upstream credentials.
6. Gateway returns bounded structured data and records the audit event.
```

## Docker communication

Same-host Coolify deployments may use an internal Docker network. Cross-host deployments must not rely on Docker bridge networks: those networks do not span hosts. Use a private routed network such as the existing lab VLAN, a VPN/Tailscale/WireGuard overlay, or an equivalent private transport.

The public/reverse-proxy interface should expose only the gateway. Node MCP ports should remain private.

## Transport

Use MCP Streamable HTTP for gateway-to-client and gateway-to-node communication. Avoid legacy SSE-only sessions for new nodes because a transport can appear connected while failing to deliver JSON-RPC responses after initialization.
