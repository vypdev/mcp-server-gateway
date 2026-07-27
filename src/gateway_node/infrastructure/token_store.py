from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import fcntl

from gateway_node.application.authentication import IssuedToken, TokenIdentity


class JsonTokenStore:
    def __init__(self, path: Path, lock_path: Path | None = None) -> None:
        self.path = path
        self.lock_path = lock_path or path.with_name(f".{path.name}.lock")

    def issue(self, client_id: str) -> IssuedToken:
        token = f"mcp_{secrets.token_urlsafe(32)}"
        with self._locked(exclusive=True):
            payload = self._read_unlocked()
            payload["tokens"].append({
                "client_id": client_id,
                "token_hash": self._digest(token),
                "created_at": datetime.now(UTC).isoformat(),
            })
            self._write_unlocked(payload)
        return IssuedToken(client_id=client_id, token=token)

    def verify(self, token: str) -> TokenIdentity | None:
        digest = self._digest(token)
        with self._locked(exclusive=False):
            records = self._read_unlocked()["tokens"]
        for record in records:
            if secrets.compare_digest(record.get("token_hash", ""), digest):
                return TokenIdentity(client_id=record["client_id"])
        return None

    def revoke(self, client_id: str) -> int:
        with self._locked(exclusive=True):
            payload = self._read_unlocked()
            remaining = [record for record in payload["tokens"] if record.get("client_id") != client_id]
            revoked = len(payload["tokens"]) - len(remaining)
            if revoked:
                payload["tokens"] = remaining
                self._write_unlocked(payload)
            return revoked

    @contextmanager
    def _locked(self, *, exclusive: bool) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_unlocked(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "tokens": []}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"cannot read token store {self.path}: {exc}") from exc
        if payload.get("version") != 1 or not isinstance(payload.get("tokens"), list):
            raise RuntimeError(f"invalid token store format: {self.path}")
        return payload

    def _write_unlocked(self, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        existing = self.path.stat() if self.path.exists() else None
        fd, temporary = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_path, existing.st_mode & 0o777 if existing else 0o640)
            if existing and hasattr(os, "chown"):
                os.chown(temporary_path, existing.st_uid, existing.st_gid)
            os.replace(temporary_path, self.path)
        finally:
            temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _digest(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
