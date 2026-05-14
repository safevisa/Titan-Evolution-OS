"""Prompt assembler — injects episodic memories + skill docs into the base prompt."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.long_term import search_memories
from app.models.domain import SkillDoc


async def build_enhanced_prompt(
    *,
    base_prompt: str,
    agent_role: str,
    tenant_id: str,
    agent_id: str,
    task_type: str,
    task_context: str,
    db: AsyncSession,
    memory_top_k: int = 3,
    skill_top_k: int = 3,
) -> str:
    """Return the base prompt enriched with relevant memories and skill docs."""

    memories = await search_memories(
        tenant_id=tenant_id,
        query=f"{task_type}: {task_context}",
        agent_id=agent_id,
        top_k=memory_top_k,
    )

    skills_q = await db.execute(
        select(SkillDoc)
        .where(SkillDoc.tenant_id == tenant_id)  # type: ignore[arg-type]
        .where(SkillDoc.role_tags.contains([agent_role]))
        .order_by(SkillDoc.success_rate.desc())
        .limit(skill_top_k)
    )
    skills = skills_q.scalars().all()

    parts: list[str] = [base_prompt.strip()]

    if memories:
        mem_block = "\n\n[Relevant past experiences]\n" + "\n---\n".join(
            f"Task: {m.get('task_type','?')} | "
            f"Success: {m.get('success_flag','?')} | "
            f"Score: {m.get('quality_score','?')}\n"
            f"Summary: {m.get('summary','')}"
            for m in memories
        )
        parts.append(mem_block)

    if skills:
        skill_block = "\n\n[Applicable SOPs]\n" + "\n---\n".join(
            f"**{s.name}** (success_rate={s.success_rate:.2f})\n"
            + "\n".join(s.content_md.splitlines()[:8])  # first 8 lines preview
            for s in skills
        )
        parts.append(skill_block)

    return "\n".join(parts)
