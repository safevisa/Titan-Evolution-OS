from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.industry_plugins import get_plugin
from app.models.domain import Agent, PerformanceLog, Task, Tenant
from app.services.task_smart_routing import infer_task_type_from_goal, pick_agent_for_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: UUID
    agent_id: UUID
    task_type: str = Field(validation_alias=AliasChoices("type", "task_type"))
    input: dict


class SmartTaskCreate(BaseModel):
    """Create a task from natural-language goal only — server infers task_type and agent."""

    tenant_id: UUID
    goal: str = Field(min_length=1, max_length=8000)
    workflow_name: Optional[str] = None
    workflow_index: Optional[int] = None


class SmartTaskResolved(BaseModel):
    task_type: str
    agent_id: UUID
    agent_name: str
    agent_role: str


class SmartTaskResponse(BaseModel):
    task: TaskRead
    resolved: SmartTaskResolved


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    tenant_id: UUID
    agent_id: UUID
    task_type: str = Field(serialization_alias="type")
    status: str
    token_used: int = 0
    duration_ms: Optional[int] = None
    output: Optional[dict] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class FeedbackBody(BaseModel):
    quality_score: float = Field(ge=0.0, le=1.0)
    human_feedback: Optional[str] = None


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    tenant_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    q = select(Task)
    if tenant_id is not None:
        q = q.where(Task.tenant_id == tenant_id)
    if status is not None:
        q = q.where(Task.status == status)
    res = await db.execute(q.order_by(Task.created_at.desc()).limit(100))
    return list(res.scalars().all())


class WorkflowTemplateRead(BaseModel):
    index: int
    name: str
    node_count: int
    roles: list[str]


@router.get("/workflow-templates", response_model=list[WorkflowTemplateRead])
async def list_workflow_templates(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[WorkflowTemplateRead]:
    """DAG templates for the tenant's industry plugin (for goal_pipeline picker)."""
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    plugin = get_plugin(tenant.industry_plugin)
    if plugin is None:
        return []
    out: list[WorkflowTemplateRead] = []
    for i, tmpl in enumerate(plugin.get_workflow_templates()):
        dag = tmpl.dag_config or {}
        nodes = dag.get("nodes", [])
        roles: list[str] = []
        for n in nodes:
            if isinstance(n, dict) and n.get("role"):
                r = str(n["role"])
                if r not in roles:
                    roles.append(r)
        out.append(
            WorkflowTemplateRead(
                index=i,
                name=tmpl.name,
                node_count=len(nodes) if isinstance(nodes, list) else 0,
                roles=roles,
            )
        )
    return out


@router.post("", response_model=TaskRead)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)) -> Task:
    if body.task_type == "goal_pipeline":
        tenant_row = await db.get(Tenant, body.tenant_id)
        if tenant_row is None:
            raise HTTPException(status_code=404, detail="tenant not found")
        agent = await db.get(Agent, body.agent_id)
        if agent is None or agent.tenant_id != body.tenant_id:
            raise HTTPException(status_code=400, detail="agent not found for this tenant")
        inp = body.input or {}
        plugin = get_plugin(tenant_row.industry_plugin)
        tmpl_list = plugin.get_workflow_templates() if plugin else []
        if tmpl_list:
            wn = inp.get("workflow_name")
            if isinstance(wn, str) and wn.strip():
                needle = wn.strip().lower()
                if not any(needle in t.name.lower() for t in tmpl_list):
                    names = [t.name for t in tmpl_list]
                    raise HTTPException(
                        status_code=400,
                        detail=f"workflow_name matched no template. Available: {names}",
                    )
            else:
                wi = inp.get("workflow_index", 0)
                try:
                    idx = int(wi)  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    idx = 0
                if idx < 0 or idx >= len(tmpl_list):
                    raise HTTPException(
                        status_code=400,
                        detail=f"workflow_index must be 0..{len(tmpl_list) - 1} for this tenant industry",
                    )

    task = Task(
        tenant_id=body.tenant_id,
        agent_id=body.agent_id,
        task_type=body.task_type,
        input=body.input,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.post("/smart", response_model=SmartTaskResponse)
async def create_smart_task(body: SmartTaskCreate, db: AsyncSession = Depends(get_db)) -> SmartTaskResponse:
    """Infer task type from ``goal`` and pick the best-matching active agent for this tenant."""
    tenant_row = await db.get(Tenant, body.tenant_id)
    if tenant_row is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    task_type = infer_task_type_from_goal(body.goal)
    agent = await pick_agent_for_task(db, body.tenant_id, task_type)
    if agent is None:
        raise HTTPException(
            status_code=400,
            detail="no active digital employees for this tenant — add agents in settings first",
        )

    inp: dict = {"goal": body.goal.strip(), "criteria": body.goal.strip()}
    if task_type == "goal_pipeline":
        plugin = get_plugin(tenant_row.industry_plugin)
        tmpl_list = plugin.get_workflow_templates() if plugin else []
        if tmpl_list:
            wn = (body.workflow_name or "").strip()
            if wn:
                needle = wn.lower()
                if not any(needle in t.name.lower() for t in tmpl_list):
                    names = [t.name for t in tmpl_list]
                    raise HTTPException(
                        status_code=400,
                        detail=f"workflow_name matched no template. Available: {names}",
                    )
                inp["workflow_name"] = wn
            else:
                wi = 0 if body.workflow_index is None else body.workflow_index
                try:
                    idx = int(wi)
                except (TypeError, ValueError):
                    idx = 0
                if idx < 0 or idx >= len(tmpl_list):
                    raise HTTPException(
                        status_code=400,
                        detail=f"workflow_index must be 0..{len(tmpl_list) - 1} for this tenant industry",
                    )
                inp["workflow_index"] = idx

    task = Task(
        tenant_id=body.tenant_id,
        agent_id=agent.id,
        task_type=task_type,
        input=inp,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return SmartTaskResponse(
        task=TaskRead.model_validate(task),
        resolved=SmartTaskResolved(
            task_type=task_type,
            agent_id=agent.id,
            agent_name=agent.name,
            agent_role=agent.role,
        ),
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/{task_id}/enqueue")
async def enqueue_task(task_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    from app.workers.tasks import enqueue_agent_task
    from app.core.plan_limits import check_task_limit

    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    if task.status not in ("pending", "failed"):
        raise HTTPException(status_code=409, detail=f"task already {task.status}")

    tenant = await db.get(Tenant, task.tenant_id)
    if tenant is not None:
        ok, msg = await check_task_limit(str(task.tenant_id), tenant.plan, db)
        if not ok:
            raise HTTPException(status_code=402, detail=msg)

    enqueue_agent_task.delay(str(task_id))
    return {"queued": True, "task_id": str(task_id)}


@router.post("/{task_id}/feedback")
async def submit_feedback(
    task_id: UUID,
    body: FeedbackBody,
    db: AsyncSession = Depends(get_db),
) -> dict:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")

    res = await db.execute(
        select(PerformanceLog).where(PerformanceLog.task_id == task_id).limit(1)
    )
    perf: PerformanceLog | None = res.scalars().first()
    if perf is None:
        perf = PerformanceLog(
            tenant_id=task.tenant_id,
            agent_id=task.agent_id,
            task_id=task.id,
            success_flag=task.status == "done",
        )
        db.add(perf)

    perf.quality_score = body.quality_score
    perf.human_feedback = body.human_feedback
    await db.commit()
    return {"ok": True, "quality_score": body.quality_score}
