from mcp_gateway.application.management import ActionResult
from mcp_gateway.domain.service import CheckResult, DoctorReport, ServiceState, ServiceStatus
from mcp_gateway.presentation.cli import main


class UninstallManagement:
    def __init__(self):
        self.calls = []

    def uninstall(self, confirmed):
        self.calls.append(confirmed)
        return ActionResult(True, True, "uninstalled")


def test_uninstall_requires_yes_in_non_interactive_mode(capsys, monkeypatch):
    management = UninstallManagement()
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    assert main(["uninstall"], management=management) == 2
    assert "--yes" in capsys.readouterr().err
    assert management.calls == []


def test_uninstall_yes_delegates_without_prompt(capsys):
    management = UninstallManagement()

    assert main(["uninstall", "--yes"], management=management) == 0
    assert "uninstalled" in capsys.readouterr().out
    assert management.calls == [True]
