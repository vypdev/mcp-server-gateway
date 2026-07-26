# Operations

## Pre-deployment

- [ ] Confirm the host runs a supported Linux version and systemd.
- [ ] Review the Unix identity selected for the profile.
- [ ] Select the profile explicitly.
- [ ] Select private bind address and unused port.
- [ ] Define filesystem paths allowed to command execution.
- [ ] Configure private transport and client authentication outside Git.
- [ ] Confirm no secrets are tracked.

## Verification

- [ ] `systemctl status` is active.
- [ ] `/healthz` returns status `ok`.
- [ ] `/readyz` reports the expected profile.
- [ ] MCP `initialize` succeeds.
- [ ] `tools/list` matches the profile contract.
- [ ] Host identity matches the target host.
- [ ] Observer calls are read-only.
- [ ] Operator commands respect timeout, path, output, and environment limits.
- [ ] Repeated calls and independent sessions work.
- [ ] Client integration is tested before enabling automation.

## Rollback

Disable the system service, restore the previous client endpoint, and preserve logs and configuration for diagnosis. Do not remove state until the rollback has been verified.
