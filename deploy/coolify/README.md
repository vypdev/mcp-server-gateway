# Coolify deployment template

This directory contains deployment guidance for the first Coolify rollout. The executable gateway image and node images will be pinned here once the implementation contract is approved.

## Recommended Coolify setup

Create one application per component:

```text
mcp-server-gateway
unifi-mcp
host-mcp-ai-core
coolify-mcp
```

Keep node applications private. Publish only the gateway through the trusted private ingress. If the gateway and node share a Coolify host, use a private Docker network. If they are on different hosts, use private routed networking or an authenticated overlay; Docker bridge networking does not span hosts.

## Environment policy

Set secrets in the Coolify application environment UI. Do not paste them into Compose files or commit them to this repository.

## First rollout

1. Deploy the gateway with no registered nodes.
2. Deploy one observer-only node.
3. Verify gateway-to-node private connectivity.
4. Register the node with its healthcheck and capability contract.
5. Test Hermes and OpenClaw independently.
6. Add the next node only after the previous node passes the operations checklist.
