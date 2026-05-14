"""Memory & Skills API — episodic memory search + skill library CRUD."""
from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.memory.long_term import search_memories
from app.models.domain import SkillDoc

router = APIRouter(prefix="/memory", tags=["memory"])


# ── Episodic memory search ──────────────────────────────────────────────────

class MemorySearchRequest(BaseModel):
    tenant_id: str
    query: str
    agent_id: Optional[str] = None
    top_k: int = 5


@router.post("/search")
async def memory_search(body: MemorySearchRequest) -> list[dict]:
    results = await search_memories(
        tenant_id=body.tenant_id,
        query=body.query,
        agent_id=body.agent_id,
        top_k=body.top_k,
    )
    return results


# ── Skill library ───────────────────────────────────────────────────────────

class SkillRead(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    tenant_id: UUID
    name: str
    description: Optional[str]
    content_md: str
    role_tags: list[str]
    industry_tags: list[str]
    usage_count: int
    success_rate: float
    is_global: bool
    version: int


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content_md: Optional[str] = None
    is_global: Optional[bool] = None


@router.get("/skills", response_model=list[SkillRead])
async def list_skills(
    tenant_id: Optional[UUID] = None,
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> list[SkillDoc]:
    q = select(SkillDoc)
    if tenant_id:
        q = q.where(SkillDoc.tenant_id == tenant_id)
    if role:
        q = q.where(SkillDoc.role_tags.contains([role]))
    if search:
        q = q.where(SkillDoc.name.ilike(f"%{search}%"))
    q = q.order_by(SkillDoc.success_rate.desc(), SkillDoc.usage_count.desc())
    res = await db.execute(q.limit(50))
    return list(res.scalars().all())


@router.get("/skills/{skill_id}", response_model=SkillRead)
async def get_skill(skill_id: UUID, db: AsyncSession = Depends(get_db)) -> SkillDoc:
    skill = await db.get(SkillDoc, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="skill not found")
    return skill


@router.put("/skills/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: UUID, body: SkillUpdate, db: AsyncSession = Depends(get_db)
) -> SkillDoc:
    skill = await db.get(SkillDoc, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="skill not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(skill, field, value)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.post("/skills/{skill_id}/promote", response_model=SkillRead)
async def promote_skill(skill_id: UUID, db: AsyncSession = Depends(get_db)) -> SkillDoc:
    """Mark a skill as global — shared with all agents in the tenant."""
    skill = await db.get(SkillDoc, skill_id)
    if skill is None:
        raise HTTPException(status_code=404, detail="skill not found")
    skill.is_global = True
    await db.commit()
    await db.refresh(skill)
    return skill
