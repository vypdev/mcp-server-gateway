from gateway_node.application.management import GatewayManagement
from gateway_node.domain.service import ActionResult, ServiceState, ServiceStatus


class FakeRemover:
    def __init__(self):
        self.calls = 0

    def remove(self):
        self.calls += 1


def test_uninstall_requires_explicit_confirmation_at_application_boundary():
    remover = FakeRemover()
    management = GatewayManagement(None, None, remover)

    result = management.uninstall(confirmed=False)

    assert result.success is False
    assert result.changed is False
    assert "confirmation" in result.message
    assert remover.calls == 0


def test_uninstall_delegates_after_confirmation():
    remover = FakeRemover()
    management = GatewayManagement(None, None, remover)

    result = management.uninstall(confirmed=True)

    assert result.success is True
    assert result.changed is True
    assert remover.calls == 1
