"""Encrypt / decrypt per-tenant integration payloads at rest (Fernet)."""
from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class IntegrationVaultError(RuntimeError):
    pass


def _fernet() -> Fernet:
    raw = settings.titan_integrations_fernet_key
    if not raw or not str(raw).strip():
        raise IntegrationVaultError(
            "Set TITAN_INTEGRATIONS_FERNET_KEY to a Fernet key "
            "(run: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\")"
        )
    key = raw.strip().encode() if isinstance(raw, str) else raw
    return Fernet(key)


def encrypt_json(payload: dict[str, Any]) -> str:
    return _fernet().encrypt(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")


def decrypt_json(blob: str) -> dict[str, Any]:
    try:
        raw = _fernet().decrypt(blob.encode("ascii"))
    except InvalidToken as e:
        raise IntegrationVaultError("invalid or corrupted integration secret") from e
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise IntegrationVaultError("invalid integration payload shape")
    return data
