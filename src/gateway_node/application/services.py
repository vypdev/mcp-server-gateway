from __future__ import annotations

from gateway_node.application.ports import CommandRunner
from gateway_node.domain.commands import CommandRequest, CommandResult
from gateway_node.domain.profiles import Profile


class ExecuteCommand:
    def __init__(self, profile: Profile, runner: CommandRunner):
        self._profile = profile
        self._runner = runner

    def run(self, request: CommandRequest) -> CommandResult:
        if not self._profile.allows_command_execution:
            raise PermissionError("command execution requires the operator profile")
        return self._runner.run(request)
