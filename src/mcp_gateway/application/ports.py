from __future__ import annotations

from typing import Protocol

from mcp_gateway.domain.commands import CommandRequest, CommandResult


class CommandRunner(Protocol):
    def run(self, request: CommandRequest) -> CommandResult:
        ...


class HostInfoProvider(Protocol):
    def identity(self) -> dict[str, object]:
        ...

    def status(self) -> dict[str, object]:
        ...
