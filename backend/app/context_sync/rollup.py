"""Daily rollup of context_sync chunks into level-1 summary nodes."""
from __future__ import annotations

import uuid
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.context_sync.config_helpers import context_sync_enabled, rollup_enabled
from app.memory.long_term import upsert_sync_point
from app.memory.token_compress import compress_for_llm
from app.memory.tree_repo import create_tree_node, find_tree_node
from app.models.domain import MemoryTreeNode, Tenant
from app.services.llm import complete_chat


def _day_key(dt: datetime | None) -> str:
    if dt is None:
        return date.today().isoformat()
    return dt.astimezone(timezone.utc).date().isoformat()


async def rollup_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> dict[str, Any]:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        return {"ok": False, "error": "tenant_not_found"}
    if not context_sync_enabled(tenant.config):
        return {"ok": True, "rolled_up": 0, "skipped": "context_sync_disabled"}
    if not rollup_enabled(tenant.config, plan=str(tenant.plan or "")):
        return {"ok": True, "rolled_up": 0, "skipped": "rollup_not_enabled"}

    q = await session.execute(
        select(MemoryTreeNode).where(
            MemoryTreeNode.tenant_id == tenant_id,
            MemoryTreeNode.level == 0,
        )
    )
    chunks = list(q.scalars().all())
    groups: dict[tuple[str, str], list[MemoryTreeNode]] = defaultdict(list)
    for node in chunks:
        groups[(node.source, _day_key(node.occurred_at))].append(node)

    rolled = 0
    tid = str(tenant_id)
    for (source, day), nodes in groups.items():
        if len(nodes) < 2:
            continue
        ext_key = f"rollup:{source}:{day}"
        existing = await find_tree_node(
            session, tenant_id=tenant_id, source=source, external_key=ext_key
        )
        if existing is not None:
            continue

        lines = [f"- {n.title}: {n.summary[:400]}" for n in nodes[:40]]
        prompt_body = "\n".join(lines)
        messages = [
            {
                "role": "system",
                "content": "Summarize the following synced items into one concise daily digest (max 800 tokens). Use bullet points.",
            },
            {"role": "user", "content": compress_for_llm(prompt_body, max_chars=24_000)},
        ]
        try:
            summary, _ = await complete_chat(messages, temperature=0.1)
        except Exception:
            summary = compress_for_llm(prompt_body, max_chars=4000)
        summary = compress_for_llm(summary or "", max_chars=8000)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"context_sync:{tid}:{ext_key}"))
        occurred = datetime.strptime(day, "%Y-%m-%d").replace(tzinfo=timezone.utc)

        parent = await create_tree_node(
            session,
            tenant_id=tenant_id,
            source=source,
            level=1,
            external_key=ext_key,
            title=f"{source} · {day}",
            summary=summary,
            qdrant_point_id=point_id,
            parent_id=None,
            token_estimate=max(1, len(summary) // 4),
            occurred_at=occurred,
        )
        parent_id = parent.id
        for child in nodes:
            child.parent_id = parent_id

        await upsert_sync_point(
            tenant_id=tid,
            point_id=point_id,
            summary=summary,
            payload={
                "source": source,
                "memory_tree_node_id": str(parent.id),
                "title": parent.title,
                "summary": summary,
                "occurred_at": occurred.isoformat(),
                "rollup_day": day,
                "child_count": len(nodes),
            },
        )
        rolled += 1

    await session.flush()
    return {"ok": True, "rolled_up": rolled}


async def rollup_all_tenants(session: AsyncSession) -> dict[str, Any]:
    q = await session.execute(select(Tenant))
    total = 0
    tenants = 0
    for tenant in q.scalars().all():
        if not context_sync_enabled(tenant.config):
            continue
        if not rollup_enabled(tenant.config, plan=str(tenant.plan or "")):
            continue
        res = await rollup_tenant(session, tenant.id)
        total += int(res.get("rolled_up", 0))
        tenants += 1
    return {"ok": True, "tenants": tenants, "rolled_up": total}
