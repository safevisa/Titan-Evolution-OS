from uuid import UUID

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    tenant_id: UUID
    agent_id: UUID
    task_type: str = Field(validation_alias=AliasChoices("type", "task_type"))
    input: dict


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    tenant_id: UUID
    agent_id: UUID
    task_type: str = Field(serialization_alias="type")
    status: str


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    tenant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> list[Task]:
    q = select(Task)
    if tenant_id is not None:
        q = q.where(Task.tenant_id == tenant_id)
    res = await db.execute(q.order_by(Task.created_at.desc()))
    return list(res.scalars().all())


@router.post("", response_model=TaskRead)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)) -> Task:
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


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)) -> Task:
    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/{task_id}/enqueue")
async def enqueue_task(task_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    from app.workers.tasks import enqueue_agent_task

    task = await db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="task not found")
    enqueue_agent_task.delay(str(task_id))
    return {"queued": True, "task_id": str(task_id)}