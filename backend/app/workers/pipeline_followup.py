"""After collaborative pipelines: schedule management follow-up when stages are skipped."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.models.domain import Agent, Task

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

MANAGER_SKILL_CLOSURE = "manager_skill_closure"


async def pick_closure_manager(db: "AsyncSession", tenant_id: uuid.UUID, coordinator: Agent) -> Agent:
    """Prefer a dedicated manager agent; fall back to the pipeline coordinator."""
    res = await db.execute(
        select(Agent)
        .where(
            Agent.tenant_id == tenant_id,
            Agent.status == "active",
            Agent.role == "manager",
        )
        .order_by(Agent.created_at.asc())
    )
    hit = res.scalars().first()
    return hit or coordinator


def _pipeline_has_skipped_stages(pipeline_out: dict) -> bool:
    stages = pipeline_out.get("stages")
    if not isinstance(stages, list):
        return False
    return any(isinstance(s, dict) and s.get("skipped") is True for s in stages)


async def _closure_already_scheduled(db: "AsyncSession", tenant_id: uuid.UUID, parent_id: uuid.UUID) -> bool:
    res = await db.execute(
        select(Task)
        .where(
            Task.tenant_id == tenant_id,
            Task.task_type == MANAGER_SKILL_CLOSURE,
        )
        .order_by(Task.created_at.desc())
        .limit(40)
    )
    pid = str(parent_id)
    for row in res.scalars():
        inp = row.input or {}
        if str(inp.get("parent_task_id") or "") == pid:
            return True
    return False


async def maybe_schedule_skill_gap_closure(
    db: "AsyncSession",
    *,
    parent_task: Task,
    pipeline_output: dict,
    coordinator: Agent,
) -> str | None:
    """If the pipeline skipped roles, enqueue a manager_skill_closure task (same DB transaction).

    Returns the new task id (str) if created, else None.
    Respects ``tenant.config['auto_skill_gap_closure']`` — default True when missing.
    """
    if not _pipeline_has_skipped_stages(pipeline_output):
        return None

    from app.models.domain import Tenant

    tenant = await db.get(Tenant, parent_task.tenant_id)
    if tenant is not None:
        cfg = tenant.config or {}
        if cfg.get("auto_skill_gap_closure") is False:
            return None

    if await _closure_already_scheduled(db, parent_task.tenant_id, parent_task.id):
        return None

    manager = await pick_closure_manager(db, parent_task.tenant_id, coordinator)
    stages = pipeline_output.get("stages") if isinstance(pipeline_output.get("stages"), list) else []
    skipped = [
        {"role": s.get("role"), "reason": s.get("reason")}
        for s in stages
        if isinstance(s, dict) and s.get("skipped")
    ]

    closure = Task(
        tenant_id=parent_task.tenant_id,
        agent_id=manager.id,
        task_type=MANAGER_SKILL_CLOSURE,
        input={
            "parent_task_id": str(parent_task.id),
            "goal": (pipeline_output.get("goal") or parent_task.input.get("goal") or ""),
            "workflow": pipeline_output.get("workflow"),
            "workflow_index": pipeline_output.get("workflow_index"),
            "stages": stages,
            "skipped_stages": skipped,
            "origin": "goal_pipeline_skill_gap",
        },
    )
    db.add(closure)
    await db.flush()
    return str(closure.id)
