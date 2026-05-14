"""Analytics endpoints — real aggregations from the DB."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import Agent, PerformanceLog, Task

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary(
    tenant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Dashboard overview: task counts, success rate, token usage, agent counts."""

    def _filter(q, model):
        if tenant_id:
            return q.where(model.tenant_id == tenant_id)
        return q

    total_q = await db.execute(_filter(select(func.count()).select_from(Task), Task))
    total_tasks: int = total_q.scalar_one()

    done_q = await db.execute(
        _filter(select(func.count()).select_from(Task), Task).where(Task.status == "done")
    )
    done_tasks: int = done_q.scalar_one()

    failed_q = await db.execute(
        _filter(select(func.count()).select_from(Task), Task).where(Task.status == "failed")
    )
    failed_tasks: int = failed_q.scalar_one()

    token_q = await db.execute(
        _filter(select(func.sum(Task.token_used)).select_from(Task), Task)
    )
    total_tokens: int = token_q.scalar_one() or 0

    agent_q = await db.execute(_filter(select(func.count()).select_from(Agent), Agent))
    total_agents: int = agent_q.scalar_one()

    active_q = await db.execute(
        _filter(select(func.count()).select_from(Agent), Agent).where(Agent.status == "active")
    )
    active_agents: int = active_q.scalar_one()

    avg_score_q = await db.execute(
        _filter(
            select(func.avg(PerformanceLog.quality_score)).select_from(PerformanceLog),
            PerformanceLog,
        ).where(PerformanceLog.quality_score.isnot(None))
    )
    avg_score: float | None = avg_score_q.scalar_one()

    success_rate = round(done_tasks / total_tasks, 3) if total_tasks else None

    return {
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "failed_tasks": failed_tasks,
        "pending_tasks": total_tasks - done_tasks - failed_tasks,
        "success_rate": success_rate,
        "total_tokens": total_tokens,
        "total_agents": total_agents,
        "active_agents": active_agents,
        "avg_quality_score": round(avg_score, 3) if avg_score else None,
    }


@router.get("/agents")
async def agent_performance(
    tenant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Per-agent task count and avg quality score."""
    q = (
        select(
            Agent.id,
            Agent.name,
            Agent.role,
            Agent.status,
            func.count(Task.id).label("task_count"),
            func.avg(PerformanceLog.quality_score).label("avg_score"),
        )
        .outerjoin(Task, Task.agent_id == Agent.id)
        .outerjoin(PerformanceLog, PerformanceLog.agent_id == Agent.id)
        .group_by(Agent.id, Agent.name, Agent.role, Agent.status)
    )
    if tenant_id:
        q = q.where(Agent.tenant_id == tenant_id)
    res = await db.execute(q)
    rows = res.all()
    return [
        {
            "id": str(r.id),
            "name": r.name,
            "role": r.role,
            "status": r.status,
            "task_count": r.task_count or 0,
            "avg_score": round(r.avg_score, 3) if r.avg_score else None,
        }
        for r in rows
    ]
