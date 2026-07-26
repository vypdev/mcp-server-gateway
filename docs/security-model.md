# Security Model

## Trust boundaries

```text
MCP client
   │ private authenticated transport
   ▼
Gateway process
   │ profile and request policy
   ▼
Unix identity
   │ operating-system permissions
   ▼
Host resources
```

The gateway does not bypass the operating-system identity. The profile limits the exposed MCP surface; the Unix identity limits the effective host capability.

## Observer

Observer is read-only:

- host identity;
- host resource status;
- bounded diagnostics;
- no model-controlled command execution;
- no self-reconfiguration;
- no privilege escalation.

## Operator

Operator adds policy-controlled command execution:

- argv execution by default;
- no implicit shell;
- approved working directories;
- bounded timeout;
- bounded output;
- filtered environment;
- audit records;
- explicit confirmation for disruptive actions.

Operator is not root by default. Any additional host privilege is external policy and must be reviewed independently.

## Transport

The endpoint must be private and authenticated. Do not expose it directly to an untrusted network. Client authentication, TLS, firewall policy, and endpoint allowlists are deployment concerns and must not be stored as secrets in this repository.

## Secrets

Never return secrets in tool output or logs. Never commit credentials, tokens, private certificates, or generated environment files.
