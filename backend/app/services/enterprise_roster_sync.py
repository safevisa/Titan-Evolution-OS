"""Sync plugin enterprise roster (agents + skills) for one tenant."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.industry_plugins import get_plugin
from app.models.domain import Agent, SkillDoc, Tenant


async def sync_tenant_enterprise_roster(db: AsyncSession, tenant_id: UUID) -> dict:
    """Ensure all plugin-defined corporate roles exist with skills; reactivate or add missing rows."""
    from app.core.plan_limits import check_agent_limit

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        return {"ok": False, "detail": "tenant not found"}
    plugin = get_plugin(tenant.industry_plugin)
    if plugin is None:
        return {"ok": False, "detail": "tenant has unknown industry_plugin"}

    res = await db.execute(select(Agent).where(Agent.tenant_id == tenant_id))
    rows = list(res.scalars().all())
    by_role: dict[str, list[Agent]] = {}
    for ag in rows:
        by_role.setdefault(ag.role, []).append(ag)

    reactivated = 0
    added = 0
    for cfg in plugin.get_agent_configs():
        lst = by_role.get(cfg.role, [])
        if any(a.status == "active" for a in lst):
            continue
        inactive = next((a for a in lst if a.status != "active"), None)
        if inactive is not None:
            inactive.status = "active"
            inactive.name = cfg.name
            inactive.current_prompt = cfg.default_prompt
            reactivated += 1
            continue
        ok, msg = await check_agent_limit(str(tenant_id), tenant.plan, db)
        if not ok:
            await db.rollback()
            return {
                "ok": False,
                "detail": msg,
                "agents_added": added,
                "agents_reactivated": reactivated,
                "skills_added": 0,
            }
        db.add(
            Agent(
                tenant_id=tenant_id,
                name=cfg.name,
                role=cfg.role,
                current_prompt=cfg.default_prompt,
            )
        )
        added += 1
        await db.flush()

    skill_res = await db.execute(select(SkillDoc.name).where(SkillDoc.tenant_id == tenant_id))
    have_names = {r[0] for r in skill_res.all()}
    skills_added = 0
    for skill in plugin.get_default_skills():
        if skill.name in have_names:
            continue
        db.add(
            SkillDoc(
                tenant_id=tenant_id,
                name=skill.name,
                content_md=skill.content_md,
                role_tags=skill.role_tags,
                industry_tags=[tenant.industry_plugin],
                is_global=False,
            )
        )
        skills_added += 1
        have_names.add(skill.name)

    await db.commit()
    active_q = await db.execute(
        select(func.count())
        .select_from(Agent)
        .where(Agent.tenant_id == tenant_id, Agent.status == "active")
    )
    active_agents = int(active_q.scalar_one() or 0)
    skill_count_q = await db.execute(
        select(func.count()).select_from(SkillDoc).where(SkillDoc.tenant_id == tenant_id)
    )
    skill_rows = int(skill_count_q.scalar_one() or 0)
    return {
        "ok": True,
        "agents_added": added,
        "agents_reactivated": reactivated,
        "skills_added": skills_added,
        "active_agents_total": active_agents,
        "skill_docs_total": skill_rows,
    }
