# Native deployment on the managed host

The production gateway for Lab01 runs directly on Lab01 as a systemd service. Coolify and Docker are managed targets; they are not the runtime for the gateway.

## Target layout

```text
ai-core
  └── Hermes/OpenClaw MCP clients

lab01
  ├── mcp-server-gateway.service
  ├── Unix identity: mcp-operator or mcp-observer
  ├── Coolify
  ├── Docker
  └── system services
```

Run one gateway instance per host. Select one fixed profile at startup:

```text
MCP_PROFILE=observer
MCP_PROFILE=operator
```

For the initial Lab01 deployment use `operator` only if the Unix identity and its groups have been reviewed. The operator profile includes observer tools.

## 1. Inspect Lab01 before installation

Run these commands on Lab01 as an administrator. Do not paste secrets into chat or Git:

```bash
id
cat /etc/os-release
command -v systemctl
python3 --version
systemctl --version
docker version
id mcp-operator
getent group docker
ss -ltnp
```

Record the results locally. Confirm the private address and choose a dedicated MCP port that is not already used.

## 2. Create the Unix identity

Create a dedicated account rather than using root:

```bash
sudo useradd --system --create-home --home-dir /var/lib/mcp-server-gateway \
  --shell /usr/sbin/nologin mcp-operator
sudo install -d -o mcp-operator -g mcp-operator -m 0750 \
  /var/lib/mcp-server-gateway /opt/mcp-server-gateway
```

Do not add the account to the `docker` group until Docker write access is explicitly accepted. Membership in `docker` is effectively root-equivalent on many hosts.

## 3. Install the application

Use a controlled checkout of the public `master` branch:

```bash
sudo git clone --branch master --depth 1 \
  https://github.com/vypdev/mcp-server-gateway.git \
  /opt/mcp-server-gateway
sudo python3 -m venv /opt/mcp-server-gateway/.venv
sudo /opt/mcp-server-gateway/.venv/bin/pip install /opt/mcp-server-gateway
sudo chown -R root:root /opt/mcp-server-gateway
sudo chmod -R a=rX /opt/mcp-server-gateway
```

The service user needs read access to the installation and write access only to its explicitly approved working directories.

## 4. Configure the fixed profile

Create `/etc/mcp-server-gateway/gateway.env` as root with mode `0600`:

```bash
sudo install -d -m 0750 -o root -g root /etc/mcp-server-gateway
sudo install -m 0600 /dev/null /etc/mcp-server-gateway/gateway.env
sudoedit /etc/mcp-server-gateway/gateway.env
```

Use values appropriate for Lab01:

```ini
MCP_HOST_ID=lab01
MCP_PROFILE=operator
MCP_HOST=<LAB01_PRIVATE_IP>
MCP_PORT=<UNUSED_PRIVATE_PORT>
MCP_ALLOWED_CWDS=/var/lib/mcp-server-gateway
MCP_COMMAND_TIMEOUT_SECONDS=30
MCP_MAX_OUTPUT_BYTES=262144
MCP_MAX_COMMAND_ARGS=64
```

Do not commit this file. Any credentials needed by future Coolify adapters remain in this root-owned file or an approved secret manager.

## 5. Install systemd

Install `deploy/systemd/mcp-server-gateway.service`:

```bash
sudo install -m 0644 deploy/systemd/mcp-server-gateway.service \
  /etc/systemd/system/mcp-server-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable --now mcp-server-gateway.service
```

Verify locally on Lab01:

```bash
systemctl status mcp-server-gateway.service --no-pager
curl --fail http://127.0.0.1:<UNUSED_PRIVATE_PORT>/healthz
curl --fail http://127.0.0.1:<UNUSED_PRIVATE_PORT>/readyz
journalctl -u mcp-server-gateway.service -n 100 --no-pager
```

## 6. Restrict network access

Allow the MCP port only from the private address of `ai-core`. Do not publish it to the Internet. Use a private VLAN, WireGuard, Tailscale, or equivalent. Add TLS and client authentication at a private reverse proxy or implement MCP authentication before exposing the endpoint beyond the trusted host network.

## 7. Verify capabilities

From Lab01, validate the effective identity:

```bash
sudo -u mcp-operator id
sudo -u mcp-operator docker ps
```

The MCP `host_get_identity` result must match the expected Lab01 host, not a container. Test `execute_command` with a harmless command first:

```json
{"argv":["id"],"cwd":"/var/lib/mcp-server-gateway","timeout_seconds":5}
```

Then test read-only Docker, service status, and bounded logs. Do not enable disruptive operations until repeated MCP sessions succeed.

## Rollback

```bash
sudo systemctl disable --now mcp-server-gateway.service
sudo rm /etc/systemd/system/mcp-server-gateway.service
sudo systemctl daemon-reload
```

Keep the previous MCP configuration unchanged until health, initialization, tool listing, repeated calls, and Hermes/OpenClaw validation all pass.
