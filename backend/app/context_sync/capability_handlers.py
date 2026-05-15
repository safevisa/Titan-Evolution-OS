"""execute_capability dispatch for context_sync_*."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.context_sync.config_helpers import context_sync_enabled
from app.context_sync.sync_service import sync_tenant_sources

_CONTEXT_SYNC_IDS = frozenset({"context_sync_run"})


async def try_context_sync_capability(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    capability_id: str,
    clean_params: dict[str, Any],
) -> tuple[bool, dict[str, Any] | None]:
    if capability_id not in _CONTEXT_SYNC_IDS:
        return False, None

    from app.models.domain import Tenant

    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        return True, {"ok": False, "error": "tenant_not_found", "capability_id": capability_id}
    if not context_sync_enabled(tenant.config):
        return True, {
            "ok": False,
            "error": "context_sync_disabled",
            "capability_id": capability_id,
            "message": "Enable tenant.config.context_sync.enabled",
        }

    raw_sources = clean_params.get("sources")
    sources: list[str] | None = None
    if isinstance(raw_sources, list) and raw_sources:
        sources = [str(s) for s in raw_sources if str(s) in ("gmail", "gcal", "github")]

    result = await sync_tenant_sources(session, tenant_id, sources=sources)  # type: ignore[arg-type]
    return True, {
        "ok": result.get("ok", False),
        "capability_id": capability_id,
        "data": result.get("data", {}),
        "error": result.get("error"),
    }
