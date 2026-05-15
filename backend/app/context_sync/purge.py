"""Purge synced data when OAuth connections are removed."""
from __future__ import annotations

import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.context_sync.sync_state_repo import upsert_sync_state
from app.memory.long_term import delete_sync_points_for_source
from app.models.domain import MemoryTreeNode

SOURCE_BY_OAUTH: dict[str, list[str]] = {
    "google_workspace_oauth": ["gmail", "gcal"],
    "github_oauth": ["github"],
}


async def purge_tenant_sources(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    sources: list[str],
) -> dict[str, int]:
    tid = str(tenant_id)
    out: dict[str, int] = {}
    for source in sources:
        qdrant_n = await delete_sync_points_for_source(tenant_id=tid, source=source)
        res = await session.execute(
            delete(MemoryTreeNode).where(
                MemoryTreeNode.tenant_id == tenant_id,
                MemoryTreeNode.source == source,
            )
        )
        out[source] = int(res.rowcount or 0) + qdrant_n
    await session.flush()
    return out


async def purge_for_oauth_provider(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    oauth_provider: str,
) -> dict[str, int]:
    sources = SOURCE_BY_OAUTH.get(oauth_provider, [])
    if not sources:
        return {}
    counts = await purge_tenant_sources(session, tenant_id, sources)
    sync_key = "google_workspace" if oauth_provider == "google_workspace_oauth" else "github"
    if oauth_provider in SOURCE_BY_OAUTH:
        await upsert_sync_state(
            session,
            tenant_id=tenant_id,
            provider=sync_key,
            cursor_json={},
            last_error=None,
            enabled=False,
        )
    return counts
