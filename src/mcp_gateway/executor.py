from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import Settings


class CommandDenied(RuntimeError):
    """The active profile or policy does not permit the command."""


@dataclass(frozen=True)
class CommandResult:
    argv: tuple[str, ...]
    cwd: str
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool


class CommandExecutor:
    def __init__(self, settings: Settings):
        self.settings = settings

    def _validate_cwd(self, cwd: str | None) -> Path:
        raw_cwd = cwd or self.settings.allowed_cwds[0]
        resolved_cwd = Path(raw_cwd).expanduser().resolve()
        if not resolved_cwd.is_dir():
            raise CommandDenied("working directory does not exist")
        allowed = tuple(Path(item).expanduser().resolve() for item in self.settings.allowed_cwds)
        if not any(resolved_cwd == root or root in resolved_cwd.parents for root in allowed):
            raise CommandDenied("working directory is outside the configured allowlist")
        return resolved_cwd

    def _validate_argv(self, argv: list[str]) -> None:
        if not argv or any("\x00" in arg for arg in argv):
            raise CommandDenied("argv must contain at least one valid argument")
        if len(argv) > self.settings.max_command_args:
            raise CommandDenied("too many command arguments")

    @staticmethod
    def _bounded(value: bytes, limit: int) -> str:
        truncated = len(value) > limit
        text = value[:limit].decode("utf-8", errors="replace")
        return text + ("\n[output truncated]" if truncated else "")

    def _run(self, argv: list[str], *, cwd: str | None, timeout_seconds: float | None) -> CommandResult:
        resolved_cwd = self._validate_cwd(cwd)
        timeout = timeout_seconds or self.settings.command_timeout_seconds
        if timeout <= 0 or timeout > self.settings.command_timeout_seconds:
            raise CommandDenied("timeout exceeds the configured command policy")

        env = {
            "PATH": os.getenv("PATH", "/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }
        process = subprocess.Popen(
            argv,
            cwd=resolved_cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            shell=False,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            timed_out = True
        return CommandResult(
            argv=tuple(argv),
            cwd=str(resolved_cwd),
            returncode=None if timed_out else process.returncode,
            stdout=self._bounded(stdout, self.settings.max_output_bytes),
            stderr=self._bounded(stderr, self.settings.max_output_bytes),
            timed_out=timed_out,
        )

    def run_readonly(
        self,
        argv: list[str],
        *,
        cwd: str | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        """Run a gateway-owned fixed read-only command, never model-provided input."""
        self._validate_argv(argv)
        return self._run(argv, cwd=cwd, timeout_seconds=timeout_seconds)

    def run(
        self,
        argv: list[str],
        *,
        cwd: str | None = None,
        timeout_seconds: float | None = None,
    ) -> CommandResult:
        if not self.settings.can_execute_commands:
            raise CommandDenied("command execution requires the operator profile")
        self._validate_argv(argv)
        return self._run(argv, cwd=cwd, timeout_seconds=timeout_seconds)
