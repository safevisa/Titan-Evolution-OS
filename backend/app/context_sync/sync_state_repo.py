"""CRUD for integration_sync_states (M02 uses)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import IntegrationSyncState


async def get_sync_state(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    provider: str,
) -> IntegrationSyncState | None:
    q = await session.execute(
        select(IntegrationSyncState).where(
            IntegrationSyncState.tenant_id == tenant_id,
            IntegrationSyncState.provider == provider,
        )
    )
    return q.scalar_one_or_none()


async def upsert_sync_state(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    provider: str,
    cursor_json: dict[str, Any] | None = None,
    last_success_at: datetime | None = None,
    last_error: str | None = None,
    enabled: bool | None = None,
) -> IntegrationSyncState:
    row = await get_sync_state(session, tenant_id, provider)
    now = datetime.now(timezone.utc)
    if row is None:
        row = IntegrationSyncState(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            provider=provider,
            cursor_json=cursor_json or {},
            last_success_at=last_success_at,
            last_error=last_error,
            enabled=True if enabled is None else enabled,
        )
        session.add(row)
    else:
        if cursor_json is not None:
            row.cursor_json = cursor_json
        if last_success_at is not None:
            row.last_success_at = last_success_at
        if last_error is not None:
            row.last_error = last_error
        if enabled is not None:
            row.enabled = enabled
        row.updated_at = now
    await session.flush()
    return row
