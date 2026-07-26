from __future__ import annotations

import subprocess
from dataclasses import dataclass

from mcp_gateway.domain.service import ServiceState, ServiceStatus


class ServiceCommandError(RuntimeError):
    """The service manager could not complete an operation."""


@dataclass(frozen=True)
class SystemdServiceController:
    service_name: str = "mcp-server-gateway.service"
    command: str = "systemctl"

    def status(self) -> ServiceStatus:
        active = self._run("is-active", self.service_name, check=False)
        enabled = self._run("is-enabled", self.service_name, check=False)
        properties = self._run(
            "show",
            self.service_name,
            "--property=MainPID,SubState,ActiveState",
            check=False,
        )
        values = self._properties(properties.stdout)
        active_state = values.get("ActiveState", active.stdout.strip())
        sub_state = values.get("SubState", active.stdout.strip())
        if active_state == "active":
            state = ServiceState.ACTIVE
        elif active_state == "failed":
            state = ServiceState.FAILED
        elif active_state in {"inactive", "deactivating"}:
            state = ServiceState.INACTIVE
        else:
            state = ServiceState.UNKNOWN
        main_pid = self._parse_pid(values.get("MainPID"))
        return ServiceStatus(
            state=state,
            enabled=enabled.returncode == 0,
            active=state is ServiceState.ACTIVE,
            summary=sub_state or active_state or "unknown",
            main_pid=main_pid,
        )

    def start(self) -> None:
        self._run("start", self.service_name)

    def stop(self) -> None:
        self._run("stop", self.service_name)

    def restart(self) -> None:
        self._run("restart", self.service_name)

    def disable(self) -> None:
        self._run("disable", "--now", self.service_name, check=False)

    def daemon_reload(self) -> None:
        self._run("daemon-reload")

    def _run(self, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        try:
            result = subprocess.run(
                [self.command, *arguments],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            raise ServiceCommandError(f"unable to run {self.command}: {exc}") from exc
        if check and result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "unknown error"
            raise ServiceCommandError(f"systemd operation failed: {detail}")
        return result

    @staticmethod
    def _properties(output: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for line in output.splitlines():
            key, separator, value = line.partition("=")
            if separator:
                values[key] = value
        return values

    @staticmethod
    def _parse_pid(value: str | None) -> int | None:
        try:
            pid = int(value or "0")
        except ValueError:
            return None
        return pid or None
