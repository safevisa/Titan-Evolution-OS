"""Plan limits — enforce max agents and monthly tasks per tenant plan."""
from __future__ import annotations

_LIMITS = {
    "starter":    {"max_agents": 64,   "max_tasks_per_month": 500},
    "growth":     {"max_agents": 120,  "max_tasks_per_month": 5_000},
    "enterprise": {"max_agents": 250, "max_tasks_per_month": 50_000},
}
_DEFAULT = _LIMITS["starter"]


def get_limits(plan: str) -> dict:
    return _LIMITS.get(plan, _DEFAULT)


async def check_agent_limit(
    tenant_id: str,
    plan: str,
    db,
) -> tuple[bool, str]:
    from sqlalchemy import func, select
    from app.models.domain import Agent

    limits = get_limits(plan)
    res = await db.execute(
        select(func.count()).select_from(Agent)
        .where(Agent.tenant_id == tenant_id)  # type: ignore[arg-type]
        .where(Agent.status == "active")
    )
    count = res.scalar_one()
    if count >= limits["max_agents"]:
        return False, f"Plan '{plan}' allows max {limits['max_agents']} agents (current: {count})"
    return True, ""


async def check_task_limit(
    tenant_id: str,
    plan: str,
    db,
) -> tuple[bool, str]:
    from datetime import datetime, timezone
    from sqlalchemy import func, select
    from app.models.domain import BillingRecord

    limits = get_limits(plan)
    now = datetime.now(tz=timezone.utc)
    res = await db.execute(
        select(BillingRecord)
        .where(BillingRecord.tenant_id == tenant_id)  # type: ignore[arg-type]
        .where(BillingRecord.period_year == now.year)
        .where(BillingRecord.period_month == now.month)
        .limit(1)
    )
    record = res.scalars().first()
    used = record.tasks_count if record else 0
    if used >= limits["max_tasks_per_month"]:
        return False, (
            f"Plan '{plan}' allows max {limits['max_tasks_per_month']} tasks/month "
            f"(used: {used})"
        )
    return True, ""
