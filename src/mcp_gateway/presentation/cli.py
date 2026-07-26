from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from mcp_gateway.application.authentication import AuthenticationService
from mcp_gateway.application.management import GatewayManagement
from mcp_gateway.application.ports import DiagnosticsProvider
from mcp_gateway.domain.service import ActionResult, DoctorReport, ServiceStatus
from mcp_gateway.infrastructure.diagnostics import SystemDiagnostics
from mcp_gateway.infrastructure.installation_remover import SystemInstallationRemover
from mcp_gateway.infrastructure.systemd_controller import ServiceCommandError, SystemdServiceController
from mcp_gateway.infrastructure.token_store import JsonTokenStore

_COMMANDS = ("doctor", "status", "start", "restart", "stop", "uninstall", "authenticate", "revoke")
_AUTH_COMMANDS = {"authenticate", "revoke"}


def main(
    argv: Sequence[str] | None = None,
    *,
    management: GatewayManagement | None = None,
    diagnostics: DiagnosticsProvider | None = None,
    auth_service: AuthenticationService | None = None,
) -> int:
    parser = argparse.ArgumentParser(prog="mcp-gateway", description="Manage the MCP Server Gateway service")
    parser.add_argument("command", choices=_COMMANDS)
    parser.add_argument("client_id", nargs="?", help="client label for authenticate/revoke")
    parser.add_argument("--yes", action="store_true", help="confirm destructive uninstall")
    args = parser.parse_args(argv)
    if args.yes and args.command != "uninstall":
        parser.error("--yes is only valid with uninstall")
    if args.command in _AUTH_COMMANDS and not args.client_id:
        parser.error(f"{args.command} requires a client label")
    if args.command not in _AUTH_COMMANDS and args.client_id:
        parser.error("client label is only valid with authenticate or revoke")

    if args.command in _AUTH_COMMANDS:
        if auth_service is None:
            if os.geteuid() != 0:
                print("error: authentication changes require root; use sudo mcp-gateway", file=sys.stderr)
                return 1
            auth_service = AuthenticationService(JsonTokenStore(
                Path("/etc/mcp-server-gateway/tokens.json"),
                Path("/var/lib/mcp-server-gateway/.tokens.json.lock"),
            ))
        try:
            if args.command == "authenticate":
                issued = auth_service.authenticate(args.client_id)
                print(f"client: {issued.client_id}")
                print(f"token: {issued.token}")
                print("warning: copy this token now; it will not be shown again")
                return 0
            revoked = auth_service.revoke(args.client_id)
            print(f"client: {args.client_id}")
            print(f"revoked: {revoked}")
            return 0
        except (ValueError, OSError, RuntimeError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1

    if management is None:
        if args.command == "uninstall" and os.geteuid() != 0:
            print("error: uninstall requires root; use sudo mcp-gateway uninstall", file=sys.stderr)
            return 1
        controller = SystemdServiceController()
        diagnostics = diagnostics or SystemDiagnostics(controller)
        remover = SystemInstallationRemover(controller)
        management = GatewayManagement(controller, diagnostics, remover)

    try:
        if args.command == "uninstall":
            if not args.yes:
                if not sys.stdin.isatty():
                    print("error: non-interactive uninstall requires --yes", file=sys.stderr)
                    return 2
                answer = input("This removes the service, installation, configuration, and state. Type UNINSTALL to continue: ")
                if answer.strip() != "UNINSTALL":
                    print("uninstall cancelled", file=sys.stderr)
                    return 1
            return _print_action(management.uninstall(confirmed=True))
        if args.command == "doctor":
            report = diagnostics.run() if diagnostics is not None else management.doctor()
            return _print_doctor(report)
        if args.command == "status":
            return _print_status(management.status())
        result = getattr(management, args.command)()
        return _print_action(result)
    except (ServiceCommandError, OSError, RuntimeError) as exc:
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
