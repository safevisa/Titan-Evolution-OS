"""Qdrant-backed episodic memory — embeds and retrieves past task experiences."""
from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any

from qdrant_client.http import models as qm

from app.core.qdrant_client import get_qdrant

_DIM = 1536
_COLLECTION_PREFIX = "agent_memories"


def _col(tenant_id: str) -> str:
    return f"{_COLLECTION_PREFIX}_{tenant_id.replace('-', '')}"


async def _ensure_collection(tenant_id: str) -> None:
    q = get_qdrant()
    col = _col(tenant_id)
    existing = [c.name for c in q.get_collections().collections]
    if col not in existing:
        q.create_collection(
            collection_name=col,
            vectors_config=qm.VectorParams(size=_DIM, distance=qm.Distance.COSINE),
        )


async def _embed(text: str) -> list[float]:
    """Get embedding via OpenAI; fall back to a deterministic mock vector."""
    try:
        from openai import AsyncOpenAI

        from app.core.config import settings

        if not settings.openai_api_key:
            raise ValueError("no key")
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.embeddings.create(
            model="text-embedding-3-small", input=text[:8000]
        )
        return resp.data[0].embedding
    except Exception:
        # Deterministic fallback — same text ⇒ same vector (demo / no-key env)
        h = hashlib.sha256(text.encode()).digest()
        base = [((b / 255.0) - 0.5) * 2 for b in h]
        repeated = (base * (_DIM // len(base) + 1))[:_DIM]
        norm = (sum(x**2 for x in repeated) ** 0.5) or 1.0
        return [x / norm for x in repeated]


async def save_memory(
    *,
    tenant_id: str,
    agent_id: str,
    task_id: str,
    task_type: str,
    summary: str,
    success_flag: bool,
    quality_score: float | None = None,
    tags: list[str] | None = None,
) -> None:
    await _ensure_collection(tenant_id)
    vector = await _embed(summary)
    point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{task_id}:memory"))
    payload: dict[str, Any] = {
        "agent_id": agent_id,
        "task_id": task_id,
        "task_type": task_type,
        "summary": summary,
        "success_flag": success_flag,
        "quality_score": quality_score,
        "timestamp": time.time(),
        "tags": tags or [],
    }
    get_qdrant().upsert(
        collection_name=_col(tenant_id),
        points=[qm.PointStruct(id=point_id, vector=vector, payload=payload)],
    )


async def search_memories(
    *,
    tenant_id: str,
    query: str,
    agent_id: str | None = None,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    await _ensure_collection(tenant_id)
    vector = await _embed(query)
    filt = None
    if agent_id:
        filt = qm.Filter(
            must=[qm.FieldCondition(key="agent_id", match=qm.MatchValue(value=agent_id))]
        )
    hits = get_qdrant().search(
        collection_name=_col(tenant_id),
        query_vector=vector,
        query_filter=filt,
        limit=top_k,
        with_payload=True,
    )
    return [{"score": h.score, **h.payload} for h in hits]
