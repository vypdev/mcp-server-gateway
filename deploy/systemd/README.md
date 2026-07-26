# Native systemd deployment

This directory contains the supported production installation path for a Linux host. The gateway runs as a native systemd service.

```bash
sudo ./scripts/setup.sh --profile observer
sudo ./scripts/setup.sh --profile operator
```

The setup script is intentionally conservative: it does not grant additional host privileges, change network policy, expose the service publicly, or overwrite an existing environment file without an explicit flag.
