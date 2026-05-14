"""Billing service — accumulates usage per tenant per month and calculates cost."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import BillingRecord

# Pricing per plan (USD)
_PRICING = {
    "starter":    {"task": 0.01,  "token_per_1k": 0.002, "agent_per_month": 5.0},
    "growth":     {"task": 0.008, "token_per_1k": 0.0015, "agent_per_month": 3.0},
    "enterprise": {"task": 0.005, "token_per_1k": 0.001,  "agent_per_month": 1.5},
}
_DEFAULT_PRICING = _PRICING["starter"]


def _price(plan: str, tasks: int, tokens: int, agents_peak: int) -> float:
    p = _PRICING.get(plan, _DEFAULT_PRICING)
    return (
        tasks * p["task"]
        + (tokens / 1000) * p["token_per_1k"]
        + agents_peak * p["agent_per_month"]
    )


async def record_task_usage(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    plan: str,
    tokens: int,
    agents_count: int,
) -> None:
    """Upsert the current month's billing record for one completed task."""
    now = datetime.now(tz=timezone.utc)
    year, month = now.year, now.month

    res = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id == tenant_id)
        .where(BillingRecord.period_year == year)
        .where(BillingRecord.period_month == month)
        .limit(1)
    )
    record: BillingRecord | None = res.scalars().first()

    if record is None:
        record = BillingRecord(
            tenant_id=tenant_id,
            period_year=year,
            period_month=month,
        )
        db.add(record)

    record.tasks_count += 1
    record.tokens_used += tokens
    record.agents_peak = max(record.agents_peak, agents_count)
    record.cost_usd = _price(plan, record.tasks_count, record.tokens_used, record.agents_peak)
    await db.commit()


async def get_billing_history(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    months: int = 6,
) -> list[dict]:
    res = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id == tenant_id)
        .order_by(BillingRecord.period_year.desc(), BillingRecord.period_month.desc())
        .limit(months)
    )
    rows = res.scalars().all()
    return [
        {
            "period": f"{r.period_year}-{r.period_month:02d}",
            "tasks_count": r.tasks_count,
            "tokens_used": r.tokens_used,
            "agents_peak": r.agents_peak,
            "cost_usd": round(r.cost_usd, 4),
        }
        for r in rows
    ]
