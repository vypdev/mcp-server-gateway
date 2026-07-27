from gateway_node.domain.service import CheckResult, DoctorReport, ServiceState, ServiceStatus
from gateway_node.presentation.cli import main


class FakeManagement:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def status(self):
        self.calls.append("status")
        return self.result

    def start(self):
        self.calls.append("start")
        return self.result

    def restart(self):
        self.calls.append("restart")
        return self.result

    def stop(self):
        self.calls.append("stop")
        return self.result


class FakeDiagnostics:
    def __init__(self, report):
        self.report = report
        self.calls = 0

    def run(self):
        self.calls += 1
        return self.report


def test_status_command_prints_state(capsys):
    status = ServiceStatus(ServiceState.ACTIVE, True, True, "active", main_pid=123)
    management = FakeManagement(status)
    assert main(["status"], management=management) == 0
    output = capsys.readouterr().out
    assert "active" in output
    assert "123" in output
    assert management.calls == ["status"]


def test_start_command_prints_idempotent_result(capsys):
    from gateway_node.application.management import ActionResult

    management = FakeManagement(ActionResult(True, False, "service already running"))
    assert main(["start"], management=management) == 0
    assert "already running" in capsys.readouterr().out
    assert management.calls == ["start"]


def test_doctor_returns_failure_when_any_check_fails(capsys):
    diagnostics = FakeDiagnostics(DoctorReport((
        CheckResult("unit", True, "present"),
        CheckResult("health", False, "unreachable"),
    )))
    assert main(["doctor"], diagnostics=diagnostics) == 1
    output = capsys.readouterr().out
    assert "[ok] unit: present" in output
    assert "[error] health: unreachable" in output
    assert diagnostics.calls == 1
