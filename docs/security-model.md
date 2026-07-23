# Security Model

## Observer

Default for Hermes, OpenClaw, monitoring agents, and security auditors:

- host status;
- Docker container inventory;
- service status;
- bounded logs;
- healthchecks;
- UniFi inventory and health;
- Coolify application status.

No mutation and no arbitrary command execution.

## Operator

Separate profile for controlled maintenance:

- restart one allowlisted service;
- restart one allowlisted container;
- run one named healthcheck;
- trigger one predefined maintenance action.

Every action requires confirmation, an audit record, an idempotency key where possible, and a bounded result.

## Admin

Disabled by default. Requires:

- separate gateway policy;
- explicit user approval;
- maintenance window where applicable;
- rollback plan;
- post-change health verification;
- audit review.

## Prohibited defaults

- `exec(command: string)`;
- unrestricted Docker socket access;
- host filesystem mounts such as `/`;
- forwarding private credentials to the model;
- exposing node endpoints publicly;
- using a public endpoint without authentication;
- enabling writes globally because one agent needs one action.
