"""Encrypt / decrypt per-tenant integration payloads at rest (Fernet, optional dual-key)."""
from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class IntegrationVaultError(RuntimeError):
    pass


def _fernet_keys() -> list[bytes]:
    keys: list[bytes] = []
    primary = (settings.titan_integrations_fernet_key or "").strip()
    if primary:
        keys.append(primary.encode() if isinstance(primary, str) else primary)
    previous = (settings.titan_integrations_fernet_key_previous or "").strip()
    if previous:
        prev_b = previous.encode() if isinstance(previous, str) else previous
        if prev_b not in keys:
            keys.append(prev_b)
    if not keys:
        raise IntegrationVaultError(
            "Set TITAN_INTEGRATIONS_FERNET_KEY to a Fernet key "
            '(run: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")'
        )
    return keys


def _primary_fernet() -> Fernet:
    return Fernet(_fernet_keys()[0])


def encrypt_json(payload: dict[str, Any]) -> str:
    return _primary_fernet().encrypt(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")


def decrypt_json(blob: str) -> dict[str, Any]:
    raw_blob = blob.encode("ascii")
    last_err: Exception | None = None
    for key in _fernet_keys():
        try:
            raw = Fernet(key).decrypt(raw_blob)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise IntegrationVaultError("invalid integration payload shape")
            return data
        except InvalidToken as e:
            last_err = e
            continue
    raise IntegrationVaultError("invalid or corrupted integration secret") from last_err


def rewrap_secret_blob(blob: str) -> str | None:
    """
    Decrypt with any configured key and re-encrypt with primary.
    Returns new blob when rotation applies; None if already on primary.
    """
    data = decrypt_json(blob)
    new_blob = encrypt_json(data)
    return new_blob if new_blob != blob else None
