# Native deployment on a managed host

The production gateway runs directly on the host it manages as a systemd service.

## Target layout

```text
MCP clients
  └── Native Gateway Node on a managed host
        ├── Unix identity: mcp-observer or mcp-operator
        ├── operating-system adapters
        ├── service integrations
        └── explicitly allowed filesystem paths
```

Run one gateway instance per host with one fixed startup profile:

```text
MCP_PROFILE=observer
MCP_PROFILE=operator
```

Before installation, confirm the host provides Linux, systemd, APT on Debian/Ubuntu when Python dependencies need installation, and an unused private bind address/port:

```bash
id
cat /etc/os-release
command -v systemctl
python3 --version
systemctl --version
ss -ltnp
```

The shortest supported installation path is:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/vypdev/gateway-node/master/install.sh)"
```

The bootstrap clones the selected repository revision into a temporary directory, runs `scripts/setup.sh`, and removes the temporary checkout. The inspected clone-and-run path remains supported:

```bash
git clone --branch master --depth 1 \
  https://github.com/vypdev/gateway-node.git
cd gateway-node
sudo ./scripts/setup.sh --profile observer
```

For an operator deployment:

```bash
sudo ./scripts/setup.sh --profile operator
```

The script is idempotent. It will:

- validate Linux, Python, and systemd prerequisites;
- create the matching Unix identity when missing;
- install the application into `/opt/gateway-node`;
- create a virtual environment;
- install the package;
- create a root-owned environment file if missing;
- install a profile-specific systemd unit;
- enable and start the service;
- verify the local health endpoint.

The script does not grant additional host privileges, alter network policy, or overwrite an existing environment file without an explicit reconfiguration flag.

## Review generated configuration

The setup script creates:

```text
/etc/gateway-node/gateway.env
/etc/systemd/system/gateway-node.service
/opt/gateway-node/.venv/
/var/lib/gateway-node/
```

Review `/etc/gateway-node/gateway.env` before exposing the endpoint:

```ini
MCP_HOST_ID=<stable-host-identifier>
MCP_PROFILE=observer
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_ALLOWED_CWDS=/var/lib/gateway-node
MCP_COMMAND_TIMEOUT_SECONDS=30
MCP_MAX_OUTPUT_BYTES=262144
MCP_MAX_COMMAND_ARGS=64
MCP_AUTH_FILE=/etc/gateway-node/tokens.json
```

For remote clients, bind to a private interface and restrict the firewall to approved client addresses. Do not bind publicly without private transport and authentication.

## Service management

The setup also installs `/usr/local/bin/gateway-node`. Use it for lifecycle and diagnostics:

```bash
gateway-node doctor
gateway-node status
sudo gateway-node start
sudo gateway-node restart
sudo gateway-node stop
sudo gateway-node authenticate openclaw
sudo gateway-node authenticate hermes
sudo gateway-node revoke openclaw
sudo gateway-node uninstall --yes
```

`systemctl enable --now` makes the service start automatically at boot. `Restart=on-failure` recovers from unexpected process failures and ordinary host reboots. `uninstall` is destructive: it requires root and explicit confirmation, and removes only the Unix service account that this installer created and marked.

## Verify the native identity

```bash
systemctl status gateway-node.service --no-pager
curl --fail http://127.0.0.1:8000/healthz
curl --fail http://127.0.0.1:8000/readyz
journalctl -u gateway-node.service -n 100 --no-pager
```

The `host_get_identity` result must identify the actual host and expected Unix UID. In operator mode, start with a harmless command:

```json
{"argv":["id"],"cwd":"/var/lib/gateway-node","timeout_seconds":5}
```

Then test read-only diagnostics and bounded command execution. Do not grant extra host privileges until the resulting capability boundary is explicitly accepted.

## Network and authentication

Expose the MCP endpoint only over a private authenticated transport. The gateway now requires a per-client Bearer token on `/mcp`; `/healthz` and `/readyz` remain local supervision endpoints. Allow the service port only from approved client addresses. For a LAN deployment, combine `--bind <private-host-ip>`, a verified unused port, a firewall allowlist, and a token stored only in the client secret environment.

## Rollback

```bash
sudo systemctl disable --now gateway-node.service
sudo rm -f /etc/systemd/system/gateway-node.service
sudo systemctl daemon-reload
```

Keep the previous client configuration unchanged until health, initialization, tool listing, repeated calls, and client validation all pass.
