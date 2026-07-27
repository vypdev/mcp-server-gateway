from dataclasses import dataclass

from gateway_node.application.authentication import IssuedToken
from gateway_node.presentation.cli import main


@dataclass
class FakeAuth:
    issued: IssuedToken
    revoked_client: str | None = None

    def authenticate(self, client_id: str) -> IssuedToken:
        self.issued = IssuedToken(client_id=client_id, token="mcp_test_token")
        return self.issued

    def revoke(self, client_id: str) -> int:
        self.revoked_client = client_id
        return 2


def test_authenticate_prints_new_token(capsys):
    auth = FakeAuth(IssuedToken(client_id="initial", token="initial-token"))

    assert main(["authenticate", "openclaw"], auth_service=auth) == 0

    output = capsys.readouterr().out
    assert "client: openclaw" in output
    assert "token: mcp_test_token" in output


def test_revoke_prints_count(capsys):
    auth = FakeAuth(IssuedToken(client_id="initial", token="initial-token"))

    assert main(["revoke", "openclaw"], auth_service=auth) == 0

    assert auth.revoked_client == "openclaw"
    assert "revoked: 2" in capsys.readouterr().out
