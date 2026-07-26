from mcp_gateway.application.management import GatewayManagement
from mcp_gateway.domain.service import ServiceState, ServiceStatus


class FakeController:
    def __init__(self, active=False):
        self.active = active
        self.enabled = True
        self.calls = []

    def status(self):
        return ServiceStatus(
            state=ServiceState.ACTIVE if self.active else ServiceState.INACTIVE,
            enabled=self.enabled,
            active=self.active,
            summary="active" if self.active else "inactive",
        )

    def start(self):
        self.calls.append("start")
        self.active = True

    def stop(self):
        self.calls.append("stop")
        self.active = False

    def restart(self):
        self.calls.append("restart")
        self.active = True


def test_start_is_idempotent_when_service_is_active():
    controller = FakeController(active=True)
    result = GatewayManagement(controller, lambda: ()).start()
    assert result.changed is False
    assert "already running" in result.message
    assert controller.calls == []


def test_start_starts_inactive_service_and_verifies_state():
    controller = FakeController(active=False)
    result = GatewayManagement(controller, lambda: ()).start()
    assert result.changed is True
    assert result.success is True
    assert controller.calls == ["start"]


def test_stop_is_idempotent_when_service_is_inactive():
    controller = FakeController(active=False)
    result = GatewayManagement(controller, lambda: ()).stop()
    assert result.changed is False
    assert "already stopped" in result.message
    assert controller.calls == []


def test_restart_always_requests_restart_and_verifies_state():
    controller = FakeController(active=True)
    result = GatewayManagement(controller, lambda: ()).restart()
    assert result.success is True
    assert result.changed is True
    assert controller.calls == ["restart"]
