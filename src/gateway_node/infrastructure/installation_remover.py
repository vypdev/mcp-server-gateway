from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from gateway_node.infrastructure.diagnostics import InstallationLayout
from gateway_node.infrastructure.systemd_controller import SystemdServiceController


@dataclass(frozen=True)
class SystemInstallationRemover:
    controller: SystemdServiceController
    layout: InstallationLayout = InstallationLayout()
    cli_path: Path = Path("/usr/local/bin/gateway-node")

    @property
    def marker_path(self) -> Path:
        return self.layout.config_file.parent / "managed-user"

    def remove(self) -> None:
        if os.geteuid() != 0:
            raise PermissionError("uninstall requires root")
        managed_user = self._read_managed_user()
        self.controller.disable()
        self._remove_path(self.layout.service_file)
        self.controller.daemon_reload()
        self._remove_path(self.cli_path, expected_target=Path("/opt/gateway-node/.venv/bin/gateway-node"))
        self._remove_path(self.layout.config_file)
        self._remove_path(self.layout.auth_file)
        self._remove_path(self.layout.auth_lock_file)
        self._remove_path(self.marker_path)
        self._remove_config_backups()
        self._remove_tree(self.layout.install_dir)
        self._remove_tree(self.layout.state_dir)
        self._remove_empty_directory(self.layout.config_file.parent)
        if managed_user is not None:
            self._remove_user(managed_user)

    def _read_managed_user(self) -> str | None:
        try:
            values = self._parse_marker(self.marker_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        if values.get("MCP_SERVICE_USER_CREATED") != "1":
            return None
        user = values.get("MCP_SERVICE_USER")
        if user not in {"mcp-observer", "mcp-operator"}:
            return None
        return user

    @staticmethod
    def _parse_marker(content: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for line in content.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key] = value
        return values

    @staticmethod
    def _remove_path(path: Path, expected_target: Path | None = None) -> None:
        if not path.exists() and not path.is_symlink():
            return
        if path.is_symlink():
            if expected_target is not None and Path(os.readlink(path)) != expected_target:
                raise RuntimeError(f"refusing to remove unmanaged symlink: {path}")
            path.unlink()
            return
        if expected_target is not None:
            raise RuntimeError(f"refusing to remove unmanaged file: {path}")
        if path.is_file():
            path.unlink()

    @staticmethod
    def _remove_tree(path: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return
        if path.is_symlink():
            raise RuntimeError(f"refusing to remove symlinked directory: {path}")
        if path.is_dir():
            shutil.rmtree(path)

    def _remove_config_backups(self) -> None:
        for backup in self.layout.config_file.parent.glob("gateway.env.bak.*"):
            if backup.is_file() and not backup.is_symlink():
                backup.unlink()

    @staticmethod
    def _remove_empty_directory(path: Path) -> None:
        try:
            path.rmdir()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    @staticmethod
    def _remove_user(user: str) -> None:
        result = subprocess.run(
            ["userdel", "--remove", user],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise RuntimeError(f"failed to remove managed Unix user {user}: {detail}")
