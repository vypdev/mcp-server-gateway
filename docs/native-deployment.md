# Native deployment on a managed host

The production gateway runs directly on the host it manages as a systemd service.

## Target layout

```text
MCP clients
  └── Native MCP Server Gateway on a managed host
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

Before installation, confirm the host provides Linux, systemd, Python 3.11+, and an unused private bind address/port:

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
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/vypdev/mcp-server-gateway/master/install.sh)"
```

The bootstrap clones the selected repository revision into a temporary directory, runs `scripts/setup.sh`, and removes the temporary checkout. The inspected clone-and-run path remains supported:

```bash
git clone --branch master --depth 1 \
  https://github.com/vypdev/mcp-server-gateway.git
cd mcp-server-gateway
sudo ./scripts/setup.sh --profile observer
```

For an operator deployment:

```bash
sudo ./scripts/setup.sh --profile operator
```

The script is idempotent. It will:

- validate Linux, Python, and systemd prerequisites;
- create the matching Unix identity when missing;
- install the application into `/opt/mcp-server-gateway`;
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
/etc/mcp-server-gateway/gateway.env
/etc/systemd/system/mcp-server-gateway.service
/opt/mcp-server-gateway/.venv/
/var/lib/mcp-server-gateway/
```

Review `/etc/mcp-server-gateway/gateway.env` before exposing the endpoint:

```ini
MCP_HOST_ID=<stable-host-identifier>
MCP_PROFILE=observer
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_ALLOWED_CWDS=/var/lib/mcp-server-gateway
MCP_COMMAND_TIMEOUT_SECONDS=30
MCP_MAX_OUTPUT_BYTES=262144
MCP_MAX_COMMAND_ARGS=64
```

For remote clients, bind to a private interface and restrict the firewall to approved client addresses. Do not bind publicly without private transport and authentication.

## Service management

The setup also installs `/usr/local/bin/mcp-gateway`. Use it for lifecycle and diagnostics:

```bash
mcp-gateway doctor
mcp-gateway status
sudo mcp-gateway start
sudo mcp-gateway restart
sudo mcp-gateway stop
```

`systemctl enable --now` makes the service start automatically at boot. `Restart=on-failure` recovers from unexpected process failures and ordinary host reboots.

## Verify the native identity

```bash
systemctl status mcp-server-gateway.service --no-pager
curl --fail http://127.0.0.1:8000/healthz
curl --fail http://127.0.0.1:8000/readyz
journalctl -u mcp-server-gateway.service -n 100 --no-pager
```

The `host_get_identity` result must identify the actual host and expected Unix UID. In operator mode, start with a harmless command:

```json
{"argv":["id"],"cwd":"/var/lib/mcp-server-gateway","timeout_seconds":5}
```

Then test read-only diagnostics and bounded command execution. Do not grant extra host privileges until the resulting capability boundary is explicitly accepted.

## Network and authentication

Expose the MCP endpoint only over a private authenticated transport. Allow the service port only from approved client addresses. Add TLS and client authentication at a private reverse proxy or implement MCP authentication before exposing the endpoint outside the trusted network.

## Rollback

```bash
sudo systemctl disable --now mcp-server-gateway.service
sudo rm -f /etc/systemd/system/mcp-server-gateway.service
sudo systemctl daemon-reload
```

Keep the previous client configuration unchanged until health, initialization, tool listing, repeated calls, and client validation all pass.
