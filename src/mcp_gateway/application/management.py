from __future__ import annotations

from mcp_gateway.application.ports import DiagnosticsProvider, ServiceController
from mcp_gateway.domain.service import ActionResult, DoctorReport, ServiceStatus


class GatewayManagement:
    def __init__(self, controller: ServiceController, diagnostics: DiagnosticsProvider):
        self._controller = controller
        self._diagnostics = diagnostics

    def status(self) -> ServiceStatus:
        return self._controller.status()

    def start(self) -> ActionResult:
        if self._controller.status().active:
            return ActionResult(True, False, "service already running")
        self._controller.start()
        return self._after_change("started")

    def stop(self) -> ActionResult:
        if not self._controller.status().active:
            return ActionResult(True, False, "service already stopped")
        self._controller.stop()
        return self._after_change("stopped", expect_active=False)

    def restart(self) -> ActionResult:
        self._controller.restart()
        return self._after_change("restarted")

    def doctor(self) -> DoctorReport:
        return self._diagnostics.run()

    def _after_change(self, verb: str, *, expect_active: bool = True) -> ActionResult:
        status = self._controller.status()
        if status.active is expect_active:
            return ActionResult(True, True, f"service {verb} successfully")
        return ActionResult(False, True, f"service failed to become {'active' if expect_active else 'inactive'}")
