"""Per-tenant token quota enforcement using Redis counters (1-minute window)."""
from __future__ import annotations

from app.core.redis_client import get_redis

# Tokens per minute per plan
_PLAN_LIMITS: dict[str, int] = {
    "starter": 20_000,
    "growth": 100_000,
    "enterprise": 500_000,
}
_DEFAULT_LIMIT = 20_000


async def check_and_consume(tenant_id: str, plan: str, tokens: int) -> tuple[bool, int]:
    """
    Attempts to consume `tokens` from the tenant's 1-minute bucket.
    Returns (allowed, remaining).
    """
    limit = _PLAN_LIMITS.get(plan, _DEFAULT_LIMIT)
    key = f"ratelimit:llm:{tenant_id}"
    r = get_redis()

    pipe = r.pipeline()
    await pipe.incr(key, tokens)
    await pipe.expire(key, 60)
    results = await pipe.execute()
    current: int = results[0]

    if current > limit:
        return False, 0
    return True, limit - current


async def get_usage(tenant_id: str) -> int:
    r = get_redis()
    val = await r.get(f"ratelimit:llm:{tenant_id}")
    return int(val) if val else 0
