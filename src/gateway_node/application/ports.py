from __future__ import annotations

from typing import Protocol

from gateway_node.domain.commands import CommandRequest, CommandResult
from gateway_node.domain.service import DoctorReport, ServiceStatus


class CommandRunner(Protocol):
    def run(self, request: CommandRequest) -> CommandResult:
        ...


class HostInfoProvider(Protocol):
    def identity(self) -> dict[str, object]:
        ...

    def status(self) -> dict[str, object]:
        ...


class ServiceController(Protocol):
    def status(self) -> ServiceStatus:
        ...

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def restart(self) -> None:
        ...


class DiagnosticsProvider(Protocol):
    def run(self) -> DoctorReport:
        ...


class InstallationRemover(Protocol):
    def remove(self) -> None:
        ...
