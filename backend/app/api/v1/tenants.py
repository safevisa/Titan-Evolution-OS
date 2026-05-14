"""Tenant management — create with auto-provisioned agents and seed skills."""
from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.industry_plugins import get_plugin, list_plugins
from app.models.domain import Agent, SkillDoc, Tenant

router = APIRouter(prefix="/tenants", tags=["tenants"])


class TenantCreate(BaseModel):
    name: str
    industry_plugin: str = "payment_fintech"
    plan: str = "starter"
    auto_provision: bool = True   # create default agents + skills from plugin


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    industry_plugin: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    reprovision_agents: bool = Field(
        default=False,
        description="Archive existing agents, delete tenant skill docs, seed from current industry plugin.",
    )


class TenantRead(BaseModel):
    model_config = {"from_attributes": True}
    id: UUID
    name: str
    industry_plugin: str
    plan: str


class TenantDetail(TenantRead):
    agents_created: int = 0
    skills_seeded: int = 0


@router.get("", response_model=list[TenantRead])
async def list_tenants(db: AsyncSession = Depends(get_db)) -> list[Tenant]:
    res = await db.execute(select(Tenant).order_by(Tenant.created_at.desc()))
    return list(res.scalars().all())


@router.get("/plugins/list")
async def available_plugins() -> list[dict]:
    return list_plugins()


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: UUID,
    body: TenantUpdate,
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    plugin_for_seed = get_plugin(tenant.industry_plugin)

    if body.name is not None:
        tenant.name = body.name

    if body.industry_plugin is not None:
        p = get_plugin(body.industry_plugin)
        if p is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown plugin '{body.industry_plugin}'. "
                f"Available: {[x['plugin_id'] for x in list_plugins()]}",
            )
        tenant.industry_plugin = body.industry_plugin
        plugin_for_seed = p

    if body.config is not None:
        merged = dict(tenant.config or {})
        merged.update(body.config)
        tenant.config = merged

    if body.reprovision_agents:
        if plugin_for_seed is None:
            raise HTTPException(status_code=400, detail="Cannot reprovision without a valid industry plugin")
        res = await db.execute(select(Agent).where(Agent.tenant_id == tenant_id))
        for ag in res.scalars().all():
            ag.status = "inactive"
        for cfg in plugin_for_seed.get_agent_configs():
            db.add(
                Agent(
                    tenant_id=tenant.id,
                    name=cfg.name,
                    role=cfg.role,
                    current_prompt=cfg.default_prompt,
                )
            )
        await db.execute(delete(SkillDoc).where(SkillDoc.tenant_id == tenant_id))
        for skill in plugin_for_seed.get_default_skills():
            db.add(
                SkillDoc(
                    tenant_id=tenant.id,
                    name=skill.name,
                    content_md=skill.content_md,
                    role_tags=skill.role_tags,
                    industry_tags=[tenant.industry_plugin],
                    is_global=False,
                )
            )

    await db.commit()
    await db.refresh(tenant)
    return tenant


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(tenant_id: UUID, db: AsyncSession = Depends(get_db)) -> Tenant:
    t = await db.get(Tenant, tenant_id)
    if t is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return t


@router.post("", response_model=TenantDetail)
async def create_tenant(
    body: TenantCreate, db: AsyncSession = Depends(get_db)
) -> TenantDetail:
    plugin = get_plugin(body.industry_plugin)
    if plugin is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown plugin '{body.industry_plugin}'. "
                   f"Available: {[p['plugin_id'] for p in list_plugins()]}",
        )

    tenant = Tenant(
        name=body.name,
        industry_plugin=body.industry_plugin,
        plan=body.plan,
    )
    db.add(tenant)
    await db.flush()  # get tenant.id before creating agents

    agents_created = 0
    skills_seeded = 0

    if body.auto_provision:
        # Create default agents from plugin config
        for cfg in plugin.get_agent_configs():
            agent = Agent(
                tenant_id=tenant.id,
                name=cfg.name,
                role=cfg.role,
                current_prompt=cfg.default_prompt,
            )
            db.add(agent)
            agents_created += 1

        # Seed default skill docs
        for skill in plugin.get_default_skills():
            sd = SkillDoc(
                tenant_id=tenant.id,
                name=skill.name,
                content_md=skill.content_md,
                role_tags=skill.role_tags,
                industry_tags=[body.industry_plugin],
                is_global=False,
            )
            db.add(sd)
            skills_seeded += 1

    await db.commit()
    await db.refresh(tenant)

    return TenantDetail(
        id=tenant.id,
        name=tenant.name,
        industry_plugin=tenant.industry_plugin,
        plan=tenant.plan,
        agents_created=agents_created,
        skills_seeded=skills_seeded,
    )


@router.get("/{tenant_id}/quota")
async def get_tenant_quota(
    tenant_id: UUID, db: AsyncSession = Depends(get_db)
) -> dict:
    from app.core.quota import get_usage

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    used = await get_usage(str(tenant_id))
    from app.core.quota import _PLAN_LIMITS, _DEFAULT_LIMIT  # noqa: PLC0415
    limit = _PLAN_LIMITS.get(tenant.plan, _DEFAULT_LIMIT)
    return {
        "tenant_id": str(tenant_id),
        "plan": tenant.plan,
        "tokens_used_this_minute": used,
        "limit_per_minute": limit,
    }
