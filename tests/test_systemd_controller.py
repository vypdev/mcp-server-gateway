import subprocess

from gateway_node.domain.service import ServiceState
from gateway_node.infrastructure.systemd_controller import SystemdServiceController


def completed(args, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def test_systemd_status_parses_active_enabled_and_pid(monkeypatch):
    def fake_run(args, **kwargs):
        if args[1] == "is-active":
            return completed(args, stdout="active\n")
        if args[1] == "is-enabled":
            return completed(args, stdout="enabled\n")
        return completed(args, stdout="MainPID=321\nSubState=running\nActiveState=active\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    status = SystemdServiceController().status()
    assert status.state is ServiceState.ACTIVE
    assert status.enabled is True
    assert status.main_pid == 321


def test_systemd_status_distinguishes_failed_service(monkeypatch):
    def fake_run(args, **kwargs):
        if args[1] == "is-active":
            return completed(args, returncode=3, stdout="failed\n")
        if args[1] == "is-enabled":
            return completed(args, returncode=1, stdout="disabled\n")
        return completed(args, stdout="MainPID=0\nSubState=failed\nActiveState=failed\n")

    monkeypatch.setattr(subprocess, "run", fake_run)
    status = SystemdServiceController().status()
    assert status.state is ServiceState.FAILED
    assert status.active is False
    assert status.enabled is False
