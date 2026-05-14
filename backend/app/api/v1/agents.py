from uuid import UUID

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.domain import Agent, PromptVersion, Tenant

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/enterprise-catalog")
async def enterprise_agent_catalog() -> dict:
    """Read-only: full corporate roster (54 roles) and SOP skills shipped with Titan OS."""
    from app.industry_data.enterprise_roster import get_corporate_agent_configs, get_corporate_skills

    agents = get_corporate_agent_configs()
    skills = get_corporate_skills()
    return {
        "agent_count": len(agents),
        "skill_count": len(skills),
        "agents": [{"role": c.role, "name": c.name} for c in agents],
        "skills": [{"name": s.name, "role_tags": list(s.role_tags)} for s in skills],
    }


class AgentCreate(BaseModel):
    tenant_id: UUID
    name: str
    role: str
    current_prompt: str


class AgentRead(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    role: str
    status: str
    prompt_version: int

    model_config = {"from_attributes": True}


@router.get("", response_model=list[AgentRead])
async def list_agents(
    tenant_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> list[Agent]:
    q = select(Agent)
    if tenant_id is not None:
        q = q.where(Agent.tenant_id == tenant_id)
    res = await db.execute(q.order_by(Agent.created_at.desc()))
    return list(res.scalars().all())


@router.post("", response_model=AgentRead)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)) -> Agent:
    from app.core.plan_limits import check_agent_limit

    tenant = await db.get(Tenant, body.tenant_id)
    if tenant is not None:
        ok, msg = await check_agent_limit(str(body.tenant_id), tenant.plan, db)
        if not ok:
            raise HTTPException(status_code=402, detail=msg)

    agent = Agent(
        tenant_id=body.tenant_id,
        name=body.name,
        role=body.role,
        current_prompt=body.current_prompt,
    )
    db.add(agent)
    await db.flush()
    db.add(
        PromptVersion(
            agent_id=agent.id,
            version=1,
            content=body.current_prompt,
        )
    )
    await db.commit()
    await db.refresh(agent)
    return agent
