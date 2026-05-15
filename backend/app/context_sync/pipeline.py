"""Ingest fetched items into memory_tree_nodes + Qdrant."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.context_sync.models import FetchedItem, IngestStats
from app.memory.long_term import upsert_sync_point
from app.memory.token_compress import compress_for_llm
from app.memory.tree_repo import create_tree_node, find_tree_node


def _chunk_text(text: str, *, max_chars: int = 12_000) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + max_chars])
        start += max_chars
    return chunks


def _token_estimate(text: str) -> int:
    return max(1, len(text) // 4)


async def ingest_items(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    items: list[FetchedItem],
) -> IngestStats:
    stats = IngestStats()
    tid = str(tenant_id)

    for item in items:
        try:
            existing = await find_tree_node(
                session,
                tenant_id=tenant_id,
                source=item.source,
                external_key=item.external_id,
            )
            if existing and existing.occurred_at == item.occurred_at:
                stats.skipped += 1
                continue

            compressed_root = compress_for_llm(item.body_text)
            chunks = _chunk_text(compressed_root)
            parent_id: uuid.UUID | None = existing.parent_id if existing else None

            for idx, chunk in enumerate(chunks):
                ext_key = item.external_id if len(chunks) == 1 else f"{item.external_id}#chunk_{idx}"
                summary = compress_for_llm(chunk, max_chars=8000)
                point_id = str(
                    uuid.uuid5(uuid.NAMESPACE_URL, f"context_sync:{tid}:{item.source}:{ext_key}")
                )
                if idx == 0 and existing is not None:
                    existing.title = item.title
                    existing.summary = summary
                    existing.qdrant_point_id = point_id
                    existing.token_estimate = _token_estimate(summary)
                    existing.occurred_at = item.occurred_at
                    node = existing
                    await session.flush()
                else:
                    node = await create_tree_node(
                        session,
                        tenant_id=tenant_id,
                        source=item.source,
                        level=0,
                        external_key=ext_key,
                        title=item.title,
                        summary=summary,
                        qdrant_point_id=point_id,
                        parent_id=parent_id,
                        token_estimate=_token_estimate(summary),
                        occurred_at=item.occurred_at,
                    )
                if parent_id is None:
                    parent_id = node.id

                occurred_iso = (
                    item.occurred_at.astimezone(timezone.utc).isoformat()
                    if item.occurred_at
                    else datetime.now(timezone.utc).isoformat()
                )
                await upsert_sync_point(
                    tenant_id=tid,
                    point_id=point_id,
                    summary=summary,
                    payload={
                        "source": item.source,
                        "memory_tree_node_id": str(node.id),
                        "title": item.title[:500],
                        "summary": summary,
                        "occurred_at": occurred_iso,
                    },
                )
                stats.ingested += 1
        except Exception as e:
            stats.errors.append(f"{item.source}:{item.external_id}:{str(e)[:120]}")

    return stats
