from pathlib import Path
from subprocess import CompletedProcess

from mcp_gateway.infrastructure.diagnostics import InstallationLayout
from mcp_gateway.infrastructure.installation_remover import SystemInstallationRemover


class FakeController:
    def __init__(self):
        self.disabled = False
        self.reloaded = False

    def disable(self):
        self.disabled = True

    def daemon_reload(self):
        self.reloaded = True


def test_remover_deletes_managed_artifacts_and_created_user(tmp_path, monkeypatch):
    install = tmp_path / "install"
    state = tmp_path / "state"
    config_dir = tmp_path / "etc"
    config = config_dir / "gateway.env"
    service = tmp_path / "mcp-server-gateway.service"
    cli = tmp_path / "mcp-gateway"
    install.mkdir()
    state.mkdir()
    config_dir.mkdir()
    config.write_text("MCP_PROFILE=observer\n")
    (config_dir / "managed-user").write_text(
        "MCP_SERVICE_USER=mcp-observer\nMCP_SERVICE_USER_CREATED=1\n"
    )
    (config_dir / "gateway.env.bak.20260101000000").write_text("old\n")
    service.write_text("[Unit]\n")
    cli.symlink_to("/opt/mcp-server-gateway/.venv/bin/mcp-gateway")
    layout = InstallationLayout(install, config, service, state)
    controller = FakeController()
    remover = SystemInstallationRemover(controller, layout, cli)
    monkeypatch.setattr("mcp_gateway.infrastructure.installation_remover.os.geteuid", lambda: 0)
    userdel_calls = []

    def fake_run(args, **kwargs):
        userdel_calls.append(args)
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr("mcp_gateway.infrastructure.installation_remover.subprocess.run", fake_run)

    remover.remove()

    assert controller.disabled
    assert controller.reloaded
    assert not install.exists()
    assert not state.exists()
    assert not config.exists()
    assert not service.exists()
    assert not cli.exists()
    assert userdel_calls == [["userdel", "--remove", "mcp-observer"]]
