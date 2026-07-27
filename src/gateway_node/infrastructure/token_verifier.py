from __future__ import annotations

from mcp.server.auth.provider import AccessToken

from gateway_node.application.authentication import AuthenticationService


class LocalTokenVerifier:
    def __init__(self, authentication: AuthenticationService) -> None:
        self._authentication = authentication

    async def verify_token(self, token: str) -> AccessToken | None:
        identity = self._authentication.verify(token)
        if identity is None:
            return None
        return AccessToken(
            token=token,
            client_id=identity.client_id,
            scopes=["gateway"],
        )
