from pathlib import Path

import pytest

from gateway_node.domain.profiles import Profile
from gateway_node.infrastructure.settings import Settings


def test_settings_parse_profile_and_paths(monkeypatch):
    monkeypatch.setenv("MCP_PROFILE", "operator")
    monkeypatch.setenv("MCP_HOST_ID", "managed-host")
    monkeypatch.setenv("MCP_ALLOWED_CWDS", "/tmp:/var/lib/gateway")
    monkeypatch.setenv("MCP_PORT", "18080")

    settings = Settings.from_env()

    assert settings.profile is Profile.OPERATOR
    assert settings.host_id == "managed-host"
    assert settings.allowed_cwds == (Path("/tmp"), Path("/var/lib/gateway"))
    assert settings.port == 18080


def test_settings_reject_invalid_profile(monkeypatch):
    monkeypatch.setenv("MCP_PROFILE", "admin")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_settings_reject_invalid_port():
    with pytest.raises(ValueError, match="port"):
        Settings(port=0)
