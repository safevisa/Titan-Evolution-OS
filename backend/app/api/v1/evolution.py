"""Evolution API — KPI status, manual trigger, A/B test management."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.evolution.scorer import compute_agent_stats
from app.models.domain import ABTest, Agent, PromptVersion, Task

router = APIRouter(prefix="/evolution", tags=["evolution"])


# ── Status ─────────────────────────────────────────────────────────────────

@router.get("/status")
async def evolution_status(
    tenant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Overall evolution health: how many agents are below threshold, running tests."""
    q = select(Agent)
    if tenant_id:
        q = q.where(Agent.tenant_id == tenant_id)
    res = await db.execute(q)
    agents = res.scalars().all()

    stats_list = []
    for agent in agents:
        s = await compute_agent_stats(agent.id, db)
        stats_list.append({
            "agent_id": str(agent.id),
            "name": agent.name,
            "role": agent.role,
            "status": agent.status,
            "kpi_score": s.kpi_score,
            "sample_count": s.sample_count,
            "success_rate": s.success_rate,
            "below_threshold": s.below_threshold,
        })

    ab_q = await db.execute(
        select(ABTest).where(ABTest.status == "running")
    )
    active_tests = ab_q.scalars().all()

    tenant_completed_tasks = 0
    if tenant_id is not None:
        done_q = await db.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.tenant_id == tenant_id)
            .where(Task.status == "done")
        )
        tenant_completed_tasks = int(done_q.scalar_one() or 0)

    return {
        "agents": stats_list,
        "active_ab_tests": len(active_tests),
        "agents_below_threshold": sum(1 for s in stats_list if s["below_threshold"]),
        "tenant_completed_tasks": tenant_completed_tasks,
        "performance_log_total_samples": sum(s["sample_count"] for s in stats_list),
    }


# ── Manual trigger ──────────────────────────────────────────────────────────

@router.post("/trigger/{agent_id}")
async def trigger_evolution(agent_id: UUID) -> dict:
    """Manually kick off an evolution cycle for one agent (async via Celery)."""
    from app.workers.evolution_worker import evolve_agent

    task = evolve_agent.delay(str(agent_id))
    return {"queued": True, "celery_task_id": task.id, "agent_id": str(agent_id)}


# ── Prompt versions ─────────────────────────────────────────────────────────

class PromptVersionRead(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    agent_id: UUID
    version: int
    content: str
    avg_score: float
    task_count: int
    status: str
    evolved_reason: Optional[str]


@router.get("/agents/{agent_id}/prompt-versions", response_model=list[PromptVersionRead])
async def list_prompt_versions(
    agent_id: UUID, db: AsyncSession = Depends(get_db)
) -> list[PromptVersion]:
    res = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.agent_id == agent_id)
        .order_by(PromptVersion.version.desc())
    )
    return list(res.scalars().all())


# ── A/B tests ───────────────────────────────────────────────────────────────

class ABTestRead(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    agent_id: UUID
    variant_a_id: UUID
    variant_b_id: UUID
    status: str
    winner_id: Optional[UUID]


class ConcludeBody(BaseModel):
    force_winner: Optional[str] = None  # "a" | "b" | None


@router.get("/ab-tests", response_model=list[ABTestRead])
async def list_ab_tests(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[ABTest]:
    q = select(ABTest)
    if status:
        q = q.where(ABTest.status == status)
    res = await db.execute(q.order_by(ABTest.started_at.desc()))
    return list(res.scalars().all())


@router.get("/ab-tests/{test_id}", response_model=ABTestRead)
async def get_ab_test(test_id: UUID, db: AsyncSession = Depends(get_db)) -> ABTest:
    test = await db.get(ABTest, test_id)
    if test is None:
        raise HTTPException(status_code=404, detail="test not found")
    return test


@router.post("/ab-tests/{test_id}/conclude", response_model=ABTestRead)
async def conclude_test(
    test_id: UUID,
    body: ConcludeBody,
    db: AsyncSession = Depends(get_db),
) -> ABTest:
    from app.evolution.ab_test import conclude_ab_test

    try:
        return await conclude_ab_test(test_id, db, force_winner=body.force_winner)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
