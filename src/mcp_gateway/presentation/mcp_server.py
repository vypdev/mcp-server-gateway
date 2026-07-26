from __future__ import annotations

from typing import Any
from pathlib import Path

from pydantic import AnyHttpUrl
from mcp.server.auth.provider import TokenVerifier
from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_gateway.application.services import ExecuteCommand
from mcp_gateway.domain.commands import CommandRequest
from mcp_gateway.infrastructure.settings import Settings
from mcp_gateway.infrastructure.subprocess_runner import ExecutionDenied
from mcp_gateway.application.ports import HostInfoProvider


def create_server(
    settings: Settings,
    host_info: HostInfoProvider,
    execute_command_use_case: ExecuteCommand,
    token_verifier: TokenVerifier | None = None,
) -> FastMCP:
    auth = None
    if token_verifier is not None:
        auth = AuthSettings(
            issuer_url=AnyHttpUrl(f"http://localhost:{settings.port}"),
            resource_server_url=None,
            required_scopes=["gateway"],
        )
    server = FastMCP(
        name="mcp-server-gateway",
        instructions=(
            f"Native host gateway for {settings.host_id}. "
            f"Profile: {settings.profile.value}. "
            "Capabilities are limited by the service Unix identity and policy."
        ),
        host=settings.bind_host,
        port=settings.port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
        token_verifier=token_verifier,
        auth=auth,
    )

    @server.custom_route("/healthz", methods=["GET"])
    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "mcp-server-gateway", "host_id": settings.host_id})

    @server.custom_route("/readyz", methods=["GET"])
    async def readyz(_: Request) -> JSONResponse:
        return JSONResponse({
            "status": "ready",
            "host_id": settings.host_id,
            "profile": settings.profile.value,
            "command_execution": settings.profile.allows_command_execution,
        })

    @server.tool()
    def host_get_identity() -> dict[str, Any]:
        return host_info.identity()

    @server.tool()
    def host_get_status() -> dict[str, Any]:
        return host_info.status()

    @server.tool()
    def execute_command(
        argv: list[str],
        cwd: str | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Execute argv as the configured service Unix user in operator profile."""
        try:
            request = CommandRequest(
                argv=tuple(argv),
                cwd=None if cwd is None else Path(cwd),
                timeout_seconds=timeout_seconds,
            )
            result = execute_command_use_case.run(request)
        except (ValueError, PermissionError, ExecutionDenied, FileNotFoundError, OSError) as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": result.succeeded,
            "argv": list(result.argv),
            "cwd": str(result.cwd),
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": result.timed_out,
        }

    if not settings.profile.allows_command_execution:
        server.remove_tool("execute_command")
    return server
