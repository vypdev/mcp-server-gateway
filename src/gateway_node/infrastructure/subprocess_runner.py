from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path

from gateway_node.domain.commands import CommandRequest, CommandResult


class ExecutionDenied(RuntimeError):
    """The process request violates the host execution policy."""


@dataclass(frozen=True)
class ProcessPolicy:
    allowed_cwds: tuple[Path, ...]
    max_timeout_seconds: float = 30.0
    max_output_bytes: int = 262_144
    max_arguments: int = 64


class SubprocessCommandRunner:
    def __init__(self, policy: ProcessPolicy):
        self._policy = policy

    def run(self, request: CommandRequest) -> CommandResult:
        cwd = self._resolve_cwd(request.cwd)
        if len(request.argv) > self._policy.max_arguments:
            raise ExecutionDenied("too many command arguments")
        timeout = request.timeout_seconds or self._policy.max_timeout_seconds
        if timeout > self._policy.max_timeout_seconds:
            raise ExecutionDenied("timeout exceeds the configured execution policy")

        process = subprocess.Popen(
            request.argv,
            cwd=cwd,
            env=self._environment(),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
            shell=False,
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            return CommandResult(
                argv=request.argv,
                cwd=cwd,
                exit_code=None,
                stdout=self._bounded(stdout),
                stderr=self._bounded(stderr),
                timed_out=True,
            )
        return CommandResult(
            argv=request.argv,
            cwd=cwd,
            exit_code=process.returncode,
            stdout=self._bounded(stdout),
            stderr=self._bounded(stderr),
        )

    def _resolve_cwd(self, requested: Path | None) -> Path:
        cwd = (requested or self._policy.allowed_cwds[0]).expanduser().resolve()
        if not cwd.is_dir():
            raise ExecutionDenied("working directory does not exist")
        allowed = tuple(root.expanduser().resolve() for root in self._policy.allowed_cwds)
        if not any(cwd == root or root in cwd.parents for root in allowed):
            raise ExecutionDenied("working directory is outside the configured allowlist")
        return cwd

    @staticmethod
    def _environment() -> dict[str, str]:
        return {
            "PATH": os.getenv("PATH", "/usr/bin:/bin"),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
        }

    def _bounded(self, output: bytes) -> str:
        truncated = len(output) > self._policy.max_output_bytes
        value = output[: self._policy.max_output_bytes].decode("utf-8", errors="replace")
        return value + ("\n[output truncated]" if truncated else "")
