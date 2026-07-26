from __future__ import annotations

import os
import pwd
import stat
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from mcp_gateway.domain.service import CheckResult, DoctorReport
from mcp_gateway.infrastructure.systemd_controller import ServiceCommandError, SystemdServiceController


@dataclass(frozen=True)
class InstallationLayout:
    install_dir: Path = Path("/opt/mcp-server-gateway")
    config_file: Path = Path("/etc/mcp-server-gateway/gateway.env")
    service_file: Path = Path("/etc/systemd/system/mcp-server-gateway.service")
    state_dir: Path = Path("/var/lib/mcp-server-gateway")
    auth_file: Path = Path("/etc/mcp-server-gateway/tokens.json")
    auth_lock_file: Path = Path("/var/lib/mcp-server-gateway/.tokens.json.lock")


@dataclass(frozen=True)
class SystemDiagnostics:
    controller: SystemdServiceController
    layout: InstallationLayout = InstallationLayout()

    def run(self) -> DoctorReport:
        checks: list[CheckResult] = [
            self._path_check("service unit", self.layout.service_file, "file"),
            self._path_check("installation", self.layout.install_dir, "directory"),
            self._path_check("state directory", self.layout.state_dir, "directory"),
        ]
        config = self._read_config(checks)
        auth_file = Path(config.get("MCP_AUTH_FILE", str(self.layout.auth_file)))
        checks.append(self._path_check("token store", auth_file, "file"))
        checks.append(self._secure_token_store_check(auth_file))
        auth_lock_file = Path(config.get("MCP_AUTH_LOCK_FILE", str(self.layout.auth_lock_file)))
        checks.append(self._path_check("token store lock", auth_lock_file, "file"))
        checks.append(self._token_lock_check(auth_lock_file))
        checks.append(self._service_user_check(config))
        checks.append(self._executable_check())
        checks.extend(self._service_checks())
        checks.append(self._health_check(config))
        return DoctorReport(tuple(checks))

    @staticmethod
    def _path_check(name: str, path: Path, kind: str) -> CheckResult:
        valid = path.is_file() if kind == "file" else path.is_dir()
        return CheckResult(name, valid, str(path) if valid else f"missing {kind}: {path}")

    def _read_config(self, checks: list[CheckResult]) -> dict[str, str]:
        try:
            values = self._parse_env(self.layout.config_file.read_text(encoding="utf-8"))
        except OSError as exc:
            checks.append(CheckResult("configuration", False, f"cannot read {self.layout.config_file}: {exc}"))
            return {}
        mode = stat.S_IMODE(self.layout.config_file.stat().st_mode)
        secure = mode & 0o077 == 0
        checks.append(CheckResult(
            "configuration",
            secure,
            str(self.layout.config_file) if secure else f"permissions must be 0600 or stricter (current {mode:04o})",
        ))
        required = {"MCP_PROFILE", "MCP_HOST", "MCP_PORT", "MCP_AUTH_FILE"}
        missing = sorted(required - values.keys())
        checks.append(CheckResult("configuration keys", not missing, "required keys present" if not missing else f"missing: {', '.join(missing)}"))
        return values

    @staticmethod
    def _parse_env(content: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
        return values

    @staticmethod
    def _secure_token_store_check(path: Path) -> CheckResult:
        try:
            mode = stat.S_IMODE(path.stat().st_mode)
        except OSError as exc:
            return CheckResult("token store permissions", False, str(exc))
        secure = mode & 0o007 == 0 and mode & 0o400 != 0
        message = str(path) if secure else f"token store must be owner/group readable and world-inaccessible (current {mode:04o})"
        return CheckResult("token store permissions", secure, message)

    @staticmethod
    def _token_lock_check(path: Path) -> CheckResult:
        try:
            mode = stat.S_IMODE(path.stat().st_mode)
        except OSError as exc:
            return CheckResult("token store lock permissions", False, str(exc))
        secure = mode & 0o007 == 0 and mode & 0o660 == 0o660
        message = str(path) if secure else f"token store lock must be owner/group read-write and world-inaccessible (current {mode:04o})"
        return CheckResult("token store lock permissions", secure, message)

    @staticmethod
    def _service_user_check(config: dict[str, str]) -> CheckResult:
        profile = config.get("MCP_PROFILE")
        user = {"observer": "mcp-observer", "operator": "mcp-operator"}.get(profile or "")
        if user is None:
            return CheckResult("service user", False, f"unsupported MCP_PROFILE: {profile or '<missing>'}")
        try:
            pwd.getpwnam(user)
        except KeyError:
            return CheckResult("service user", False, f"missing Unix user: {user}")
        return CheckResult("service user", True, user)

    def _executable_check(self) -> CheckResult:
        executable = self.layout.install_dir / ".venv" / "bin" / "mcp-server-gateway"
        valid = executable.is_file() and os.access(executable, os.X_OK)
        return CheckResult("gateway executable", valid, str(executable) if valid else f"missing or not executable: {executable}")

    def _service_checks(self) -> tuple[CheckResult, ...]:
        try:
            status = self.controller.status()
        except ServiceCommandError as exc:
            return (CheckResult("service manager", False, str(exc)),)
        return (
            CheckResult("service enabled", status.enabled is True, "enabled" if status.enabled else "not enabled"),
            CheckResult("service active", status.active, status.summary),
        )

    @staticmethod
    def _health_check(config: dict[str, str]) -> CheckResult:
        host = config.get("MCP_HOST", "127.0.0.1")
        port = config.get("MCP_PORT")
        if not port or not port.isdigit():
            return CheckResult("health endpoint", False, "MCP_PORT is missing or invalid")
        if host in {"0.0.0.0", ""}:
            host = "127.0.0.1"
        elif host in {"::", "::0"}:
            host = "[::1]"
        elif ":" in host and not host.startswith("["):
            host = f"[{host}]"
        url = f"http://{host}:{port}/healthz"
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                if response.status != 200:
                    return CheckResult("health endpoint", False, f"HTTP {response.status}")
        except (OSError, urllib.error.URLError) as exc:
            return CheckResult("health endpoint", False, f"{url}: {exc}")
        return CheckResult("health endpoint", True, url)
