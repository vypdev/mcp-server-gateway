# Native deployment on a managed host

The production gateway runs directly on the host it manages as a systemd service. Coolify and Docker, when present, are managed targets; they are not the runtime for the gateway.

## Target layout

```text
MCP clients
  └── Native MCP Server Gateway on a managed host
        ├── Unix identity: mcp-observer or mcp-operator
        ├── Docker/Coolify, when enabled
        ├── system services
        └── explicitly allowed filesystem paths
```

Run one gateway instance per host. Select one fixed profile at startup:

```text
MCP_PROFILE=observer
MCP_PROFILE=operator
```

The operator profile includes observer tools. It must run under the Unix identity whose permissions define the intended operating boundary.

## 1. Inspect the target host

Run these commands on the target host as an administrator:

```bash
id
cat /etc/os-release
command -v systemctl
python3 --version
systemctl --version
command -v docker && docker version || true
getent group docker || true
ss -ltnp
```

Choose a private bind address, an unused port, and the filesystem paths the gateway may access.

## 2. Install with the setup script

Clone the repository and run the setup script as root:

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
- create `mcp-observer` or `mcp-operator` when missing;
- install the application into `/opt/mcp-server-gateway`;
- create a virtual environment;
- install the package;
- create a root-owned environment file if missing;
- install a profile-specific systemd unit;
- enable and start the service;
- verify the local health endpoint.

The script does not add the account to the `docker` group, grant sudo, modify firewall rules, or overwrite an existing environment file without an explicit reconfiguration flag.

## 3. Review generated configuration

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

For a remote MCP client, change `MCP_HOST` to the host's private interface and restrict the firewall to the client's private address. Do not bind publicly without private transport and authentication.

## 4. Verify the native identity

```bash
systemctl status mcp-server-gateway.service --no-pager
curl --fail http://127.0.0.1:8000/healthz
curl --fail http://127.0.0.1:8000/readyz
journalctl -u mcp-server-gateway.service -n 100 --no-pager
```

The MCP `host_get_identity` result must identify the actual host and expected Unix UID, not a container. In operator mode, start with a harmless command:

```json
{"argv":["id"],"cwd":"/var/lib/mcp-server-gateway","timeout_seconds":5}
```

Then test read-only service, Docker, and Coolify operations. Do not grant Docker or sudo access until the resulting capability boundary is explicitly accepted.

## 5. Network and authentication

Expose the MCP endpoint only over a private VLAN, VPN, Tailscale, WireGuard, or equivalent. Allow the MCP port only from approved client addresses. Add TLS and client authentication at a private reverse proxy or implement MCP authentication before exposing the endpoint outside the trusted network.

## Rollback

```bash
sudo systemctl disable --now mcp-server-gateway.service
sudo rm -f /etc/systemd/system/mcp-server-gateway.service
sudo systemctl daemon-reload
```

Keep the previous MCP configuration unchanged until health, initialization, tool listing, repeated calls, and client validation all pass.
