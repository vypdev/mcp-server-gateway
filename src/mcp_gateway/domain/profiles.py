from __future__ import annotations

from enum import StrEnum


class Profile(StrEnum):
    OBSERVER = "observer"
    OPERATOR = "operator"

    @property
    def allows_command_execution(self) -> bool:
        return self is Profile.OPERATOR
