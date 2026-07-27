from dataclasses import dataclass
from pathlib import Path

import pytest

from gateway_node.application.services import ExecuteCommand
from gateway_node.domain.commands import CommandRequest, CommandResult
from gateway_node.domain.profiles import Profile


@dataclass
class RecordingRunner:
    result: CommandResult
    received: CommandRequest | None = None

    def run(self, request: CommandRequest) -> CommandResult:
        self.received = request
        return self.result


def test_observer_cannot_execute_command():
    runner = RecordingRunner(CommandResult.success(("id",), Path("/tmp"), "ok\n"))
    service = ExecuteCommand(Profile.OBSERVER, runner)

    with pytest.raises(PermissionError, match="operator"):
        service.run(CommandRequest(argv=("id",)))

    assert runner.received is None


def test_operator_delegates_validated_request_to_runner():
    expected = CommandResult.success(("id",), Path("/tmp"), "uid=1000\n")
    runner = RecordingRunner(expected)
    service = ExecuteCommand(Profile.OPERATOR, runner)
    request = CommandRequest(argv=("id",), cwd=Path("/tmp"), timeout_seconds=5)

    assert service.run(request) == expected
    assert runner.received == request
