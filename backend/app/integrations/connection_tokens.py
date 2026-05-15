"""Load tenant connection secrets; refresh OAuth tokens before use."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.connections_repo import decrypt_row_secret, get_connection_row, upsert_encrypted_payload
from app.integrations.oauth_token_refresh import (
    oauth_providers_with_refresh,
    refresh_oauth_payload,
    token_needs_refresh,
)
from app.models.domain import IntegrationConnection


async def get_connection_secret(
    session: AsyncSession,
    tenant_id: UUID,
    provider: str,
    *,
    refresh_if_needed: bool = True,
) -> dict[str, Any] | None:
    """
    Decrypt connection payload; for refreshable OAuth providers, renew access_token
    when near expiry and persist encrypted payload back to DB.
    """
    row = await get_connection_row(session, tenant_id, provider)
    if row is None:
        return None
    payload = decrypt_row_secret(row)
    if not refresh_if_needed or provider not in oauth_providers_with_refresh():
        return payload
    if not token_needs_refresh(payload):
        return payload
    try:
        fresh = await refresh_oauth_payload(provider, payload)
        if fresh != payload:
            await upsert_encrypted_payload(
                session,
                tenant_id,
                provider,
                payload=fresh,
                meta=row.meta if isinstance(row.meta, dict) else None,
            )
            await session.flush()
        return fresh
    except Exception:
        return payload
