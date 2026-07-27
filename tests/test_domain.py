import pytest

from gateway_node.domain.commands import CommandRequest
from gateway_node.domain.profiles import Profile


def test_profiles_define_monotonic_command_capability():
    assert Profile.OBSERVER.allows_command_execution is False
    assert Profile.OPERATOR.allows_command_execution is True


def test_command_request_rejects_empty_argv():
    with pytest.raises(ValueError, match="argv"):
        CommandRequest(argv=())


def test_command_request_rejects_null_bytes():
    with pytest.raises(ValueError, match="NUL"):
        CommandRequest(argv=("printf", "bad\x00value"))
