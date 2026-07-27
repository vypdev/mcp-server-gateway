from starlette.testclient import TestClient

from gateway_node.application.authentication import AuthenticationService
from gateway_node.application.services import ExecuteCommand
from gateway_node.domain.profiles import Profile
from gateway_node.infrastructure.settings import Settings
from gateway_node.infrastructure.subprocess_runner import ProcessPolicy, SubprocessCommandRunner
from gateway_node.infrastructure.token_store import JsonTokenStore
from gateway_node.infrastructure.token_verifier import LocalTokenVerifier
from gateway_node.presentation.mcp_server import create_server


class FakeHostInfo:
    def identity(self):
        return {"host_id": "test-host", "uid": 1000}

    def status(self):
        return {"host_id": "test-host", "cpu_percent": 0}


def test_mcp_requires_bearer_token_but_health_is_public(tmp_path):
    settings = Settings(profile=Profile.OBSERVER, auth_file=tmp_path / "tokens.json")
    runner = SubprocessCommandRunner(ProcessPolicy(allowed_cwds=settings.allowed_cwds))
    auth = AuthenticationService(JsonTokenStore(settings.auth_file))
    issued = auth.authenticate("ai-core")
    server = create_server(
        settings,
        FakeHostInfo(),
        ExecuteCommand(settings.profile, runner),
        token_verifier=LocalTokenVerifier(auth),
    )

    with TestClient(server.streamable_http_app()) as client:
        assert client.get("/healthz").status_code == 200
        assert client.post("/mcp", json={}).status_code == 401
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "test", "version": "1"}},
            },
            headers={"Authorization": f"Bearer {issued.token}"},
        )
        assert response.status_code != 401
