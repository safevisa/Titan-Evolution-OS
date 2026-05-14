"""Redis-backed working memory — stores task context with 24-hour TTL."""
from __future__ import annotations

import json
from typing import Any

from app.core.redis_client import get_redis

_TTL = 86400  # 24 h


async def save_context(task_id: str, data: dict[str, Any]) -> None:
    r = get_redis()
    await r.setex(f"task:context:{task_id}", _TTL, json.dumps(data, default=str))


async def get_context(task_id: str) -> dict[str, Any] | None:
    r = get_redis()
    raw = await r.get(f"task:context:{task_id}")
    return json.loads(raw) if raw else None


async def delete_context(task_id: str) -> None:
    r = get_redis()
    await r.delete(f"task:context:{task_id}")


async def cache_agent_perf(agent_id: str, score: float) -> None:
    """Keep the last 50 scores in a sorted set (score = score, member = timestamp)."""
    import time

    r = get_redis()
    key = f"perf:agent:{agent_id}:recent"
    ts = time.time()
    await r.zadd(key, {str(ts): score})
    await r.zremrangebyrank(key, 0, -51)  # keep newest 50
    await r.expire(key, 7 * 86400)


async def get_recent_scores(agent_id: str) -> list[float]:
    r = get_redis()
    raw = await r.zrangebyscore(f"perf:agent:{agent_id}:recent", "-inf", "+inf")
    return [float(v) for v in raw]
