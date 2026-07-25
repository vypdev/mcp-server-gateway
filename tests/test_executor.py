import sys

import pytest

from mcp_gateway.config import Settings
from mcp_gateway.executor import CommandDenied, CommandExecutor


def test_profile_is_fixed_and_operator_is_superset(monkeypatch):
    monkeypatch.setenv("MCP_PROFILE", "operator")
    settings = Settings.from_env()
    assert settings.profile == "operator"
    assert settings.can_execute_commands is True

    monkeypatch.setenv("MCP_PROFILE", "observer")
    observer = Settings.from_env()
    assert observer.profile == "observer"
    assert observer.can_execute_commands is False


def test_observer_cannot_execute_commands(tmp_path):
    settings = Settings(profile="observer", allowed_cwds=(str(tmp_path),))
    executor = CommandExecutor(settings)
    with pytest.raises(CommandDenied, match="operator"):
        executor.run([sys.executable, "-c", "print('no')"], cwd=str(tmp_path))


def test_observer_can_run_gateway_owned_readonly_command(tmp_path):
    settings = Settings(profile="observer", allowed_cwds=(str(tmp_path),))
    executor = CommandExecutor(settings)
    result = executor.run_readonly(
        [sys.executable, "-c", "print('read-only-ok')"],
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "read-only-ok"


def test_operator_executes_as_current_process_with_bounded_output(tmp_path):
    settings = Settings(
        profile="operator",
        allowed_cwds=(str(tmp_path),),
        command_timeout_seconds=5,
        max_output_bytes=100,
    )
    executor = CommandExecutor(settings)
    result = executor.run(
        [sys.executable, "-c", "print('gateway-ok')"],
        cwd=str(tmp_path),
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "gateway-ok"
    assert result.timed_out is False


def test_operator_rejects_working_directory_outside_allowlist(tmp_path):
    settings = Settings(profile="operator", allowed_cwds=(str(tmp_path),))
    executor = CommandExecutor(settings)
    with pytest.raises(CommandDenied, match="working directory"):
        executor.run([sys.executable, "-c", "print('no')"], cwd="/")


def test_operator_enforces_timeout(tmp_path):
    settings = Settings(
        profile="operator",
        allowed_cwds=(str(tmp_path),),
        command_timeout_seconds=0.05,
    )
    executor = CommandExecutor(settings)
    result = executor.run(
        [sys.executable, "-c", "import time; time.sleep(1)"],
        cwd=str(tmp_path),
    )
    assert result.timed_out is True
    assert result.returncode is None
