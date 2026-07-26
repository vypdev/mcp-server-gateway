import json

import pytest

from mcp_gateway.application.authentication import AuthenticationService
from mcp_gateway.infrastructure.token_store import JsonTokenStore


def test_authenticate_stores_only_hash_and_verifies_token(tmp_path):
    path = tmp_path / "tokens.json"
    service = AuthenticationService(JsonTokenStore(path))

    issued = service.authenticate("ai-core")

    assert issued.client_id == "ai-core"
    assert issued.token.startswith("mcp_")
    assert service.verify(issued.token).client_id == "ai-core"
    assert issued.token not in path.read_text()
    payload = json.loads(path.read_text())
    assert payload["tokens"][0]["client_id"] == "ai-core"
    assert payload["tokens"][0]["token_hash"]


def test_authenticate_allows_multiple_tokens_and_revoke_removes_all(tmp_path):
    service = AuthenticationService(JsonTokenStore(tmp_path / "tokens.json"))

    first = service.authenticate("openclaw")
    second = service.authenticate("openclaw")
    other = service.authenticate("hermes")

    assert first.token != second.token
    assert service.revoke("openclaw") == 2
    assert service.verify(first.token) is None
    assert service.verify(second.token) is None
    assert service.verify(other.token).client_id == "hermes"


def test_client_id_is_constrained_to_safe_labels(tmp_path):
    service = AuthenticationService(JsonTokenStore(tmp_path / "tokens.json"))

    with pytest.raises(ValueError):
        service.authenticate("../etc/passwd")
    with pytest.raises(ValueError):
        service.revoke("client with spaces")


def test_revoke_unknown_client_is_idempotent(tmp_path):
    service = AuthenticationService(JsonTokenStore(tmp_path / "tokens.json"))

    assert service.revoke("missing-client") == 0
