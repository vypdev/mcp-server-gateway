# Native setup script

This directory contains the supported production installation path for a Linux host. The gateway runs as a native systemd service, not inside Coolify or Docker.

```bash
sudo ./scripts/setup.sh --profile observer
sudo ./scripts/setup.sh --profile operator
```

The script is intentionally conservative: it does not grant Docker or sudo access, change firewall rules, expose the service publicly, or overwrite an existing environment file without an explicit flag.
