from __future__ import annotations

import json
import os
import platform
import shutil
from typing import Any

import psutil
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .config import Settings
from .executor import CommandDenied, CommandExecutor


def _result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    return {"value": result}


def create_server(settings: Settings) -> FastMCP:
    mcp = FastMCP(
        name="mcp-server-gateway",
        instructions=(
            f"Host-local MCP gateway for {settings.host_id}. "
            f"Profile: {settings.profile}. "
            "Operations are limited by the gateway process Unix identity and policy."
        ),
        host=settings.bind_host,
        port=settings.port,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
    )
    executor = CommandExecutor(settings)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "mcp-server-gateway", "host_id": settings.host_id})

    @mcp.custom_route("/readyz", methods=["GET"])
    async def readyz(_: Request) -> JSONResponse:
        return JSONResponse({
            "status": "ready",
            "host_id": settings.host_id,
            "profile": settings.profile,
            "command_execution": settings.can_execute_commands,
        })

    @mcp.tool()
    def host_get_identity() -> dict[str, Any]:
        return {
            "host_id": settings.host_id,
            "hostname": platform.node(),
            "platform": platform.platform(),
            "uid": os.getuid() if hasattr(os, "getuid") else None,
            "euid": os.geteuid() if hasattr(os, "geteuid") else None,
            "profile": settings.profile,
        }

    @mcp.tool()
    def host_get_status() -> dict[str, Any]:
        disk = psutil.disk_usage("/")
        memory = psutil.virtual_memory()
        return {
            "host_id": settings.host_id,
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory": {"total": memory.total, "available": memory.available, "percent": memory.percent},
            "disk_root": {"total": disk.total, "free": disk.free, "percent": disk.percent},
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

    @mcp.tool()
    def docker_list_containers() -> dict[str, Any]:
        if not shutil.which("docker"):
            return {"ok": False, "error": "docker executable is not available in the gateway runtime"}
        try:
            value = executor.run_readonly(["docker", "ps", "--all", "--format", "{{json .}}"])
        except CommandDenied as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": value.returncode == 0,
            "returncode": value.returncode,
            "stdout": value.stdout,
            "stderr": value.stderr,
            "timed_out": value.timed_out,
        }

    @mcp.tool()
    def execute_command(
        argv: list[str],
        cwd: str | None = None,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        """Execute argv as the gateway Unix user. Available only in operator profile."""
        try:
            value = executor.run(argv, cwd=cwd, timeout_seconds=timeout_seconds)
        except (CommandDenied, FileNotFoundError, PermissionError, OSError) as exc:
            return {"ok": False, "error": str(exc)}
        return {
            "ok": value.returncode == 0 and not value.timed_out,
            "argv": list(value.argv),
            "cwd": value.cwd,
            "returncode": value.returncode,
            "stdout": value.stdout,
            "stderr": value.stderr,
            "timed_out": value.timed_out,
        }

    if not settings.can_execute_commands:
        # The function is deliberately not registered in observer mode.
        mcp.remove_tool("execute_command")

    return mcp


def main() -> None:
    settings = Settings.from_env()
    server = create_server(settings)
    server.run(transport="streamable-http")


if __name__ == "__main__":
    main()
