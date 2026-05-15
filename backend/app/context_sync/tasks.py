"""Celery tasks for Context Sync."""
from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app.workers.celery_app import celery_app


@celery_app.task(name="titan.context_sync.tick")
def tick_all_tenants() -> dict:
    return asyncio.get_event_loop().run_until_complete(_tick())


async def _tick() -> dict:
    from app.context_sync.config_helpers import context_sync_enabled
    from app.context_sync.sync_state_repo import get_sync_state
    from app.core.database import AsyncSessionLocal
    from app.integrations.connections_repo import get_connection_row
    from app.integrations.providers import PROVIDER_GITHUB_OAUTH, PROVIDER_GOOGLE_WORKSPACE_OAUTH
    from app.models.domain import Tenant

    queued: list[str] = []
    async with AsyncSessionLocal() as db:
        tenants_q = await db.execute(select(Tenant))
        for tenant in tenants_q.scalars().all():
            if not context_sync_enabled(tenant.config):
                continue
            ws = await get_connection_row(db, tenant.id, PROVIDER_GOOGLE_WORKSPACE_OAUTH)
            gh = await get_connection_row(db, tenant.id, PROVIDER_GITHUB_OAUTH)
            if ws is None and gh is None:
                continue
            ws_st = await get_sync_state(db, tenant.id, "google_workspace")
            gh_st = await get_sync_state(db, tenant.id, "github")
            if ws_st and not ws_st.enabled and gh_st and not gh_st.enabled:
                continue
            sync_tenant.delay(str(tenant.id))
            queued.append(str(tenant.id))
    return {"queued": len(queued), "tenant_ids": queued[:50]}


@celery_app.task(name="titan.context_sync.tenant")
def sync_tenant(tenant_id: str, sources: list[str] | None = None) -> dict:
    return asyncio.get_event_loop().run_until_complete(_sync_tenant(tenant_id, sources))


async def _sync_tenant(tenant_id: str, sources: list[str] | None) -> dict:
    from app.context_sync.sync_service import sync_tenant_sources
    from app.core.database import AsyncSessionLocal

    tid = uuid.UUID(tenant_id)
    async with AsyncSessionLocal() as db:
        result = await sync_tenant_sources(db, tid, sources=sources)  # type: ignore[arg-type]
        await db.commit()
        return result


@celery_app.task(name="titan.context_sync.rollup")
def rollup_all() -> dict:
    return asyncio.get_event_loop().run_until_complete(_rollup())


async def _rollup() -> dict:
    from app.context_sync.rollup import rollup_all_tenants
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await rollup_all_tenants(db)
        await db.commit()
        return result


@celery_app.task(name="titan.context_sync.purge")
def purge_tenant_source(tenant_id: str, source: str) -> dict:
    return asyncio.get_event_loop().run_until_complete(_purge(tenant_id, source))


async def _purge(tenant_id: str, source: str) -> dict:
    from app.context_sync.purge import purge_tenant_sources
    from app.core.database import AsyncSessionLocal

    tid = uuid.UUID(tenant_id)
    async with AsyncSessionLocal() as db:
        counts = await purge_tenant_sources(db, tid, [source])
        await db.commit()
        return {"ok": True, "purged": counts}
