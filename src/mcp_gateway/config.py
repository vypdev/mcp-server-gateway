from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path


_VALID_PROFILES = {"observer", "operator"}


@dataclass(frozen=True)
class Settings:
    profile: str = "observer"
    host_id: str = "unknown"
    allowed_cwds: tuple[str, ...] = ("/tmp",)
    command_timeout_seconds: float = 30.0
    max_output_bytes: int = 262_144
    max_command_args: int = 64
    bind_host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        if self.profile not in _VALID_PROFILES:
            raise ValueError(f"MCP_PROFILE must be one of {sorted(_VALID_PROFILES)}")
        if self.command_timeout_seconds <= 0:
            raise ValueError("command_timeout_seconds must be positive")
        if self.max_output_bytes <= 0:
            raise ValueError("max_output_bytes must be positive")
        if not self.allowed_cwds:
            raise ValueError("allowed_cwds must not be empty")

    @property
    def can_execute_commands(self) -> bool:
        return self.profile == "operator"

    @classmethod
    def from_env(cls) -> "Settings":
        cwds = tuple(
            str(Path(item).expanduser())
            for item in os.getenv("MCP_ALLOWED_CWDS", "/tmp").split(":")
            if item
        )
        return cls(
            profile=os.getenv("MCP_PROFILE", "observer").strip().lower(),
            host_id=os.getenv("MCP_HOST_ID", socket.gethostname()),
            allowed_cwds=cwds,
            command_timeout_seconds=float(os.getenv("MCP_COMMAND_TIMEOUT_SECONDS", "30")),
            max_output_bytes=int(os.getenv("MCP_MAX_OUTPUT_BYTES", "262144")),
            max_command_args=int(os.getenv("MCP_MAX_COMMAND_ARGS", "64")),
            bind_host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "8000")),
        )
