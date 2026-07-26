from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


_CLIENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:@/-]{0,127}$")


@dataclass(frozen=True)
class IssuedToken:
    client_id: str
    token: str


@dataclass(frozen=True)
class TokenIdentity:
    client_id: str


class CredentialStore(Protocol):
    def issue(self, client_id: str) -> IssuedToken: ...

    def verify(self, token: str) -> TokenIdentity | None: ...

    def revoke(self, client_id: str) -> int: ...


class AuthenticationService:
    def __init__(self, store: CredentialStore) -> None:
        self._store = store

    def authenticate(self, client_id: str) -> IssuedToken:
        client_id = self._validate_client_id(client_id)
        return self._store.issue(client_id)

    def verify(self, token: str) -> TokenIdentity | None:
        if not token or len(token) > 256:
            return None
        return self._store.verify(token)

    def revoke(self, client_id: str) -> int:
        return self._store.revoke(self._validate_client_id(client_id))

    @staticmethod
    def _validate_client_id(client_id: str) -> str:
        normalized = client_id.strip()
        if not _CLIENT_ID.fullmatch(normalized):
            raise ValueError(
                "client id must be 1-128 characters using letters, numbers, '.', '_', ':', '@', '/', or '-'")
        return normalized
