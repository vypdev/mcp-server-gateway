from __future__ import annotations

from mcp_gateway.application.ports import CommandRunner
from mcp_gateway.domain.commands import CommandRequest, CommandResult
from mcp_gateway.domain.profiles import Profile


class ExecuteCommand:
    def __init__(self, profile: Profile, runner: CommandRunner):
        self._profile = profile
        self._runner = runner

    def run(self, request: CommandRequest) -> CommandResult:
        if not self._profile.allows_command_execution:
            raise PermissionError("command execution requires the operator profile")
        return self._runner.run(request)
