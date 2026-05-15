"""CRUD for memory_tree_nodes (M02 pipeline uses)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import MemoryTreeNode


async def find_tree_node(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    source: str,
    external_key: str,
) -> MemoryTreeNode | None:
    q = await session.execute(
        select(MemoryTreeNode).where(
            MemoryTreeNode.tenant_id == tenant_id,
            MemoryTreeNode.source == source,
            MemoryTreeNode.external_key == external_key,
        )
    )
    return q.scalar_one_or_none()


async def create_tree_node(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    source: str,
    level: int,
    external_key: str,
    title: str,
    summary: str,
    qdrant_point_id: str | None = None,
    parent_id: uuid.UUID | None = None,
    token_estimate: int = 0,
    occurred_at: datetime | None = None,
) -> MemoryTreeNode:
    node = MemoryTreeNode(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        source=source,
        level=level,
        parent_id=parent_id,
        external_key=external_key,
        title=title,
        summary=summary,
        qdrant_point_id=qdrant_point_id,
        token_estimate=token_estimate,
        occurred_at=occurred_at,
    )
    session.add(node)
    await session.flush()
    return node
