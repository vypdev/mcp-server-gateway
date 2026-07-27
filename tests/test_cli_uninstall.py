from gateway_node.application.management import ActionResult
from gateway_node.domain.service import CheckResult, DoctorReport, ServiceState, ServiceStatus
from gateway_node.presentation.cli import main


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
