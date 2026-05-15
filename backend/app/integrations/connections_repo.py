from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.providers import ALL_MANAGED_PROVIDERS
from app.integrations.token_vault import decrypt_json, encrypt_json
from app.models.domain import IntegrationConnection


async def list_providers_for_tenant(session: AsyncSession, tenant_id: UUID) -> frozenset[str]:
    res = await session.execute(
        select(IntegrationConnection.provider).where(IntegrationConnection.tenant_id == tenant_id)
    )
    return frozenset(str(x) for x in res.scalars().all())


async def list_connections_public(session: AsyncSession, tenant_id: UUID) -> list[dict[str, Any]]:
    res = await session.execute(
        select(IntegrationConnection).where(IntegrationConnection.tenant_id == tenant_id)
    )
    rows: list[dict[str, Any]] = []
    for row in res.scalars().all():
        meta = row.meta if isinstance(row.meta, dict) else {}
        rows.append(
            {
                "provider": row.provider,
                "meta": meta,
                "created_at": row.created_at.isoformat() if row.created_at else None,
                "updated_at": row.updated_at.isoformat() if row.updated_at else None,
            }
        )
    return rows


async def get_connection_row(session: AsyncSession, tenant_id: UUID, provider: str) -> IntegrationConnection | None:
    return await session.scalar(
        select(IntegrationConnection).where(
            IntegrationConnection.tenant_id == tenant_id,
            IntegrationConnection.provider == provider,
        )
    )


async def upsert_encrypted_payload(
    session: AsyncSession,
    tenant_id: UUID,
    provider: str,
    *,
    payload: dict[str, Any],
    meta: dict[str, Any] | None = None,
) -> None:
    if provider not in ALL_MANAGED_PROVIDERS:
        raise ValueError("unknown provider")
    enc = encrypt_json(payload)
    m = dict(meta or {})
    row = await get_connection_row(session, tenant_id, provider)
    if row:
        row.secret_enc = enc
        row.meta = m
    else:
        session.add(
            IntegrationConnection(
                tenant_id=tenant_id,
                provider=provider,
                secret_enc=enc,
                meta=m,
            )
        )


async def delete_connection(session: AsyncSession, tenant_id: UUID, provider: str) -> bool:
    res = await session.execute(
        delete(IntegrationConnection).where(
            IntegrationConnection.tenant_id == tenant_id,
            IntegrationConnection.provider == provider,
        )
    )
    return res.rowcount > 0


def decrypt_row_secret(row: IntegrationConnection) -> dict[str, Any]:
    return decrypt_json(row.secret_enc)
