from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from mcp_gateway.application.management import GatewayManagement
from mcp_gateway.application.ports import DiagnosticsProvider
from mcp_gateway.domain.service import ActionResult, DoctorReport, ServiceStatus
from mcp_gateway.infrastructure.diagnostics import SystemDiagnostics
from mcp_gateway.infrastructure.systemd_controller import ServiceCommandError, SystemdServiceController

_COMMANDS = ("doctor", "status", "start", "restart", "stop")


def main(
    argv: Sequence[str] | None = None,
    *,
    management: GatewayManagement | None = None,
    diagnostics: DiagnosticsProvider | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="mcp-gateway", description="Manage the MCP Server Gateway service")
    parser.add_argument("command", choices=_COMMANDS)
    args = parser.parse_args(argv)

    if management is None:
        controller = SystemdServiceController()
        diagnostics = diagnostics or SystemDiagnostics(controller)
        management = GatewayManagement(controller, diagnostics)

    try:
        if args.command == "doctor":
            report = diagnostics.run() if diagnostics is not None else management.doctor()
            return _print_doctor(report)
        if args.command == "status":
            return _print_status(management.status())
        result = getattr(management, args.command)()
        return _print_action(result)
    except (ServiceCommandError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def _print_status(status: ServiceStatus) -> int:
    print("service: mcp-server-gateway.service")
    print(f"state: {status.state.value}")
    print(f"summary: {status.summary}")
    print(f"enabled: {_yes_no(status.enabled)}")
    print(f"active: {_yes_no(status.active)}")
    print(f"main_pid: {status.main_pid or '-'}")
    return 0


def _print_action(result: ActionResult) -> int:
    print(result.message)
    return 0 if result.success else 1


def _print_doctor(report: DoctorReport) -> int:
    for check in report.checks:
        if check.passed:
            marker = "ok"
        elif check.warning:
            marker = "warn"
        else:
            marker = "error"
        print(f"[{marker}] {check.name}: {check.message}")
    return 0 if report.passed else 1


def _yes_no(value: bool | None) -> str:
    if value is None:
        return "unknown"
    return "yes" if value else "no"


if __name__ == "__main__":
    raise SystemExit(main())
