import sys
from pathlib import Path

import pytest

from gateway_node.domain.commands import CommandRequest
from gateway_node.infrastructure.subprocess_runner import ExecutionDenied, ProcessPolicy, SubprocessCommandRunner


def runner_for(tmp_path: Path, **kwargs) -> SubprocessCommandRunner:
    return SubprocessCommandRunner(
        ProcessPolicy(allowed_cwds=(tmp_path,), **kwargs)
    )


def test_operator_runner_executes_process_as_current_user(tmp_path):
    runner = runner_for(tmp_path)
    result = runner.run(CommandRequest((sys.executable, "-c", "print('gateway-ok')"), cwd=tmp_path))
    assert result.succeeded
    assert result.stdout.strip() == "gateway-ok"


def test_runner_rejects_working_directory_outside_allowlist(tmp_path):
    runner = runner_for(tmp_path)
    with pytest.raises(ExecutionDenied, match="working directory"):
        runner.run(CommandRequest((sys.executable, "-c", "print('no')"), cwd=Path("/")))


def test_runner_enforces_timeout(tmp_path):
    runner = runner_for(tmp_path, max_timeout_seconds=0.05)
    result = runner.run(CommandRequest((sys.executable, "-c", "import time; time.sleep(1)"), cwd=tmp_path))
    assert result.timed_out
    assert result.exit_code is None


def test_runner_bounds_output(tmp_path):
    runner = runner_for(tmp_path, max_output_bytes=8)
    result = runner.run(CommandRequest((sys.executable, "-c", "print('0123456789')"), cwd=tmp_path))
    assert result.stdout.endswith("[output truncated]")
