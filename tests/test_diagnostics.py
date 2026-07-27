from gateway_node.domain.service import ServiceState, ServiceStatus
from gateway_node.infrastructure.diagnostics import InstallationLayout, SystemDiagnostics


class FakeController:
    def status(self):
        return ServiceStatus(ServiceState.ACTIVE, True, True, "running", 42)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_doctor_passes_for_complete_installation(tmp_path, monkeypatch):
    install = tmp_path / "install"
    executable = install / ".venv" / "bin" / "gateway-node-server"
    executable.parent.mkdir(parents=True)
    executable.write_text("#!/bin/sh\n")
    executable.chmod(0o755)
    state = tmp_path / "state"
    state.mkdir()
    config = tmp_path / "gateway.env"
    auth = tmp_path / "tokens.json"
    auth.write_text('{"version":1,"tokens":[]}\n')
    auth.chmod(0o640)
    lock = tmp_path / ".tokens.json.lock"
    lock.write_text("")
    lock.chmod(0o660)
    config.write_text(
        "MCP_PROFILE=observer\nMCP_HOST=127.0.0.1\nMCP_PORT=8000\n"
        f"MCP_AUTH_FILE={auth}\n"
        f"MCP_AUTH_LOCK_FILE={lock}\n"
    )
    config.chmod(0o600)
    unit = tmp_path / "service.unit"
    unit.write_text("[Service]\n")
    layout = InstallationLayout(install, config, unit, state)

    monkeypatch.setattr("gateway_node.infrastructure.diagnostics.pwd.getpwnam", lambda user: object())
    monkeypatch.setattr("gateway_node.infrastructure.diagnostics.urllib.request.urlopen", lambda *args, **kwargs: FakeResponse())

    report = SystemDiagnostics(FakeController(), layout).run()

    assert report.passed
    assert all(check.passed for check in report.checks)


def test_doctor_reports_missing_installation(tmp_path):
    layout = InstallationLayout(
        install_dir=tmp_path / "missing-install",
        config_file=tmp_path / "missing-config",
        service_file=tmp_path / "missing-unit",
        state_dir=tmp_path / "missing-state",
    )

    report = SystemDiagnostics(FakeController(), layout).run()

    assert report.passed is False
    assert any(check.name == "configuration" and not check.passed for check in report.checks)
