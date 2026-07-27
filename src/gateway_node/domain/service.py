from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ServiceState(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ServiceStatus:
    state: ServiceState
    enabled: bool | None
    active: bool
    summary: str
    main_pid: int | None = None


@dataclass(frozen=True)
class ActionResult:
    success: bool
    changed: bool
    message: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    message: str
    warning: bool = False


@dataclass(frozen=True)
class DoctorReport:
    checks: tuple[CheckResult, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed or check.warning for check in self.checks)
