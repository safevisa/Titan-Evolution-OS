"""Per-capability rate limits and usage metering (Redis + monthly rollup)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.integrations.capabilities import ToolCapability
from app.models.domain import CapabilityUsageRollup

_CATEGORY_DEFAULT_QUOTA: dict[str, int] = {
    "messaging": 120,
    "social": 60,
    "email": 40,
    "crm": 30,
    "code": 20,
}

_PLAN_QUOTA_MULTIPLIER: dict[str, float] = {
    "starter": 1.0,
    "growth": 2.5,
    "enterprise": 10.0,
}


def _quota_limit(cap: ToolCapability, plan: str) -> int:
    base = cap.quota_per_minute
    if base is None:
        base = _CATEGORY_DEFAULT_QUOTA.get(cap.category, 30)
    mult = _PLAN_QUOTA_MULTIPLIER.get(plan, 1.0)
    return max(1, int(base * mult))


async def check_capability_rate_limit(
    tenant_id: uuid.UUID,
    capability_ref: str,
    *,
    plan: str,
    cap: ToolCapability,
) -> tuple[bool, int]:
    """Returns (allowed, remaining_in_window)."""
    limit = _quota_limit(cap, plan)
    key = f"ratelimit:cap:{tenant_id}:{capability_ref}"
    r = get_redis()
    pipe = r.pipeline()
    await pipe.incr(key)
    await pipe.expire(key, 60)
    results = await pipe.execute()
    current = int(results[0])
    if current > limit:
        return False, 0
    return True, limit - current


async def record_capability_metering(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    capability_ref: str,
    cap: ToolCapability,
    ok: bool,
) -> None:
    if not ok:
        return
    now = datetime.now(tz=timezone.utc)
    year, month = now.year, now.month
    cost = float(cap.bill_unit_usd or 0.0)
    stmt = (
        insert(CapabilityUsageRollup)
        .values(
            tenant_id=tenant_id,
            period_year=year,
            period_month=month,
            capability_ref=capability_ref[:180],
            invocation_count=1,
            estimated_cost_usd=cost,
        )
        .on_conflict_do_update(
            index_elements=["tenant_id", "period_year", "period_month", "capability_ref"],
            set_={
                "invocation_count": CapabilityUsageRollup.invocation_count + 1,
                "estimated_cost_usd": CapabilityUsageRollup.estimated_cost_usd + cost,
            },
        )
    )
    await session.execute(stmt)


async def list_capability_usage(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    year: int | None = None,
    month: int | None = None,
) -> list[dict]:
    now = datetime.now(tz=timezone.utc)
    y = year or now.year
    m = month or now.month
    res = await session.execute(
        select(CapabilityUsageRollup)
        .where(
            CapabilityUsageRollup.tenant_id == tenant_id,
            CapabilityUsageRollup.period_year == y,
            CapabilityUsageRollup.period_month == m,
        )
        .order_by(CapabilityUsageRollup.invocation_count.desc())
    )
    return [
        {
            "capability_ref": row.capability_ref,
            "invocation_count": row.invocation_count,
            "estimated_cost_usd": float(row.estimated_cost_usd or 0),
        }
        for row in res.scalars().all()
    ]
