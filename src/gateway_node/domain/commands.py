from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandRequest:
    argv: tuple[str, ...]
    cwd: Path | None = None
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        if not self.argv or any(not arg or "\x00" in arg for arg in self.argv):
            raise ValueError("argv must contain non-empty arguments without NUL bytes")
        if self.timeout_seconds is not None and self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: Path
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool = False

    @classmethod
    def success(cls, argv: tuple[str, ...], cwd: Path, stdout: str = "") -> "CommandResult":
        return cls(argv=argv, cwd=cwd, exit_code=0, stdout=stdout, stderr="")

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out
