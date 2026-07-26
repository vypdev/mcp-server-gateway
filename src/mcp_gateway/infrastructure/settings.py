from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path

from mcp_gateway.domain.profiles import Profile


@dataclass(frozen=True)
class Settings:
    profile: Profile = Profile.OBSERVER
    host_id: str = "unknown"
    allowed_cwds: tuple[Path, ...] = (Path("/tmp"),)
    command_timeout_seconds: float = 30.0
    max_output_bytes: int = 262_144
    max_command_args: int = 64
    bind_host: str = "127.0.0.1"
    port: int = 8000
    auth_file: Path = Path("/etc/mcp-server-gateway/tokens.json")

    def __post_init__(self) -> None:
        if not self.allowed_cwds:
            raise ValueError("allowed_cwds must not be empty")
        if self.command_timeout_seconds <= 0:
            raise ValueError("command_timeout_seconds must be positive")
        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        if self.max_command_args <= 0:
            raise ValueError("max_command_args must be positive")
        if not 1 <= self.port <= 65_535:
            raise ValueError("port must be between 1 and 65535")

    @classmethod
    def from_env(cls) -> "Settings":
        paths = tuple(
            Path(item).expanduser()
            for item in os.getenv("MCP_ALLOWED_CWDS", "/tmp").split(":")
            if item
        )
        profile = Profile(os.getenv("MCP_PROFILE", Profile.OBSERVER.value).strip().lower())
        return cls(
            profile=profile,
            host_id=os.getenv("MCP_HOST_ID", socket.gethostname()),
            allowed_cwds=paths,
            command_timeout_seconds=float(os.getenv("MCP_COMMAND_TIMEOUT_SECONDS", "30")),
            max_output_bytes=int(os.getenv("MCP_MAX_OUTPUT_BYTES", "262144")),
            max_command_args=int(os.getenv("MCP_MAX_COMMAND_ARGS", "64")),
            bind_host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
            auth_file=Path(os.getenv("MCP_AUTH_FILE", "/etc/mcp-server-gateway/tokens.json")),
        )
