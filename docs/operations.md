# Operations

## Pre-deployment

- [ ] Repository contains no secrets.
- [ ] Gateway and node images are pinned or reproducibly built.
- [ ] Node endpoints are private.
- [ ] Observer profile is the only enabled capability.
- [ ] Gateway and each node have healthchecks.
- [ ] Coolify environment variables are configured outside Git.

## Verification

- [ ] Gateway healthcheck passes.
- [ ] Node healthcheck passes.
- [ ] MCP initialize succeeds.
- [ ] `tools/list` matches the node contract.
- [ ] Two sequential calls succeed.
- [ ] Concurrent calls do not mix responses.
- [ ] Upstream timeout returns a bounded structured error.
- [ ] Unauthorized node/tool requests are rejected.
- [ ] Hermes can connect.
- [ ] OpenClaw can connect.
- [ ] Audit logs contain no secrets.

## Rollback

Disable the node in the gateway registry, restore the previous Coolify deployment, verify gateway health, and leave the existing MCP configuration untouched until the replacement passes the complete validation matrix.
