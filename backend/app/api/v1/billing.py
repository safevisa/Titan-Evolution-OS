"""Billing, usage reporting, data export, and onboarding endpoints."""
from __future__ import annotations

import csv
import io
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.plan_limits import get_limits
from app.models.domain import Agent, BillingRecord, Contact, PerformanceLog, SkillDoc, Task, Tenant
from app.services.billing import get_billing_history

router = APIRouter(prefix="/billing", tags=["billing"])


# ── Usage summary ───────────────────────────────────────────────────────────

@router.get("/summary/{tenant_id}")
async def billing_summary(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    history = await get_billing_history(db, tenant_id, months=6)
    limits = get_limits(tenant.plan)

    # Current month usage
    current = history[0] if history else {"tasks_count": 0, "tokens_used": 0, "agents_peak": 0, "cost_usd": 0}

    # Active agents count
    agent_q = await db.execute(
        select(func.count()).select_from(Agent)
        .where(Agent.tenant_id == tenant_id)
        .where(Agent.status != "retired")
    )
    active_agents = agent_q.scalar_one()

    return {
        "tenant_id": str(tenant_id),
        "plan": tenant.plan,
        "limits": limits,
        "current_month": current,
        "active_agents": active_agents,
        "task_usage_pct": round(current["tasks_count"] / max(limits["max_tasks_per_month"], 1) * 100, 1),
        "agent_usage_pct": round(active_agents / max(limits["max_agents"], 1) * 100, 1),
        "history": history,
    }


@router.get("/plans")
async def plan_comparison() -> list[dict]:
    return [
        {
            "plan": plan,
            "max_agents": v["max_agents"],
            "max_tasks_per_month": v["max_tasks_per_month"],
        }
        for plan, v in {
            "starter":    {"max_agents": 3,   "max_tasks_per_month": 500},
            "growth":     {"max_agents": 15,  "max_tasks_per_month": 5_000},
            "enterprise": {"max_agents": 100, "max_tasks_per_month": 50_000},
        }.items()
    ]


# ── Data export ─────────────────────────────────────────────────────────────

def _stream_csv(headers: list[str], rows: list[list]) -> StreamingResponse:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers)
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"},
    )


@router.get("/export/tasks/{tenant_id}")
async def export_tasks(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    res = await db.execute(
        select(Task).where(Task.tenant_id == tenant_id).order_by(Task.created_at.desc()).limit(5000)
    )
    tasks = res.scalars().all()
    return _stream_csv(
        ["id", "type", "status", "token_used", "duration_ms", "created_at", "completed_at"],
        [
            [str(t.id), t.task_type, t.status, t.token_used,
             t.duration_ms, t.created_at, t.completed_at]
            for t in tasks
        ],
    )


@router.get("/export/contacts/{tenant_id}")
async def export_contacts(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    res = await db.execute(
        select(Contact).where(Contact.tenant_id == tenant_id).order_by(Contact.created_at.desc()).limit(5000)
    )
    contacts = res.scalars().all()
    return _stream_csv(
        ["id", "company_name", "contact_name", "email", "industry", "country",
         "company_size", "status", "score"],
        [
            [str(c.id), c.company_name, c.contact_name, c.email,
             c.industry, c.country, c.company_size, c.status, c.score]
            for c in contacts
        ],
    )


@router.get("/export/performance/{tenant_id}")
async def export_performance(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    res = await db.execute(
        select(PerformanceLog)
        .where(PerformanceLog.tenant_id == tenant_id)
        .order_by(PerformanceLog.created_at.desc())
        .limit(5000)
    )
    logs = res.scalars().all()
    return _stream_csv(
        ["id", "agent_id", "task_id", "success_flag", "quality_score",
         "token_cost", "latency_ms", "human_feedback", "created_at"],
        [
            [str(l.id), str(l.agent_id), str(l.task_id), l.success_flag,
             l.quality_score, l.token_cost, l.latency_ms, l.human_feedback, l.created_at]
            for l in logs
        ],
    )


# ── Onboarding checklist ────────────────────────────────────────────────────

@router.get("/onboarding/{tenant_id}")
async def onboarding_checklist(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    """Returns a live checklist of onboarding steps with completion status."""
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    agent_q = await db.execute(
        select(func.count()).select_from(Agent).where(Agent.tenant_id == tenant_id)
    )
    agent_count = agent_q.scalar_one()

    task_q = await db.execute(
        select(func.count()).select_from(Task).where(Task.tenant_id == tenant_id)
    )
    task_count = task_q.scalar_one()

    done_q = await db.execute(
        select(func.count()).select_from(Task)
        .where(Task.tenant_id == tenant_id)
        .where(Task.status == "done")
    )
    done_count = done_q.scalar_one()

    skill_q = await db.execute(
        select(func.count()).select_from(SkillDoc).where(SkillDoc.tenant_id == tenant_id)
    )
    skill_count = skill_q.scalar_one()

    perf_q = await db.execute(
        select(func.count()).select_from(PerformanceLog)
        .where(PerformanceLog.tenant_id == tenant_id)
        .where(PerformanceLog.quality_score.isnot(None))
    )
    feedback_count = perf_q.scalar_one()

    steps = [
        {"step": 1, "label": "Tenant created",           "done": True},
        {"step": 2, "label": "Agents provisioned",        "done": agent_count > 0,
         "detail": f"{agent_count} agent(s)"},
        {"step": 3, "label": "First task created",        "done": task_count > 0,
         "detail": f"{task_count} total"},
        {"step": 4, "label": "First task completed",      "done": done_count > 0,
         "detail": f"{done_count} done"},
        {"step": 5, "label": "Human feedback submitted",  "done": feedback_count > 0,
         "detail": f"{feedback_count} rated"},
        {"step": 6, "label": "Skills auto-generated",     "done": skill_count > 0,
         "detail": f"{skill_count} skill(s)"},
    ]
    completed = sum(1 for s in steps if s["done"])
    return {
        "tenant_id": str(tenant_id),
        "plan": tenant.plan,
        "industry_plugin": tenant.industry_plugin,
        "progress": f"{completed}/{len(steps)}",
        "complete": completed == len(steps),
        "steps": steps,
    }
