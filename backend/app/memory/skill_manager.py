"""Skill distillation — high-quality tasks become reusable SkillDocs."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import SkillDoc
from app.services.llm import complete_chat

_QUALITY_THRESHOLD = 0.8  # only distill if score ≥ this


async def maybe_create_skill(
    *,
    db: AsyncSession,
    tenant_id: uuid.UUID,
    agent_id: uuid.UUID,
    agent_role: str,
    task_type: str,
    task_input: dict,
    task_output: dict,
    quality_score: float,
) -> SkillDoc | None:
    if quality_score < _QUALITY_THRESHOLD:
        return None

    # Check if a similar skill already exists and has a higher success rate
    existing = await db.execute(
        select(SkillDoc)
        .where(SkillDoc.tenant_id == tenant_id)
        .where(SkillDoc.role_tags.contains([agent_role]))
        .order_by(SkillDoc.success_rate.desc())
        .limit(5)
    )
    similar = existing.scalars().all()
    if any(s.success_rate >= 0.9 for s in similar):
        # Increment usage count on the best skill
        best = max(similar, key=lambda s: s.success_rate)
        best.usage_count += 1
        await db.commit()
        return None

    content = await _generate_skill_doc(
        agent_role=agent_role,
        task_type=task_type,
        task_input=task_input,
        task_output=task_output,
    )
    if not content:
        return None

    title = _extract_title(content)
    skill = SkillDoc(
        tenant_id=tenant_id,
        name=title,
        content_md=content,
        role_tags=[agent_role],
        industry_tags=[],
        source_agent_id=agent_id,
        usage_count=1,
        success_rate=quality_score,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


async def _generate_skill_doc(
    agent_role: str,
    task_type: str,
    task_input: dict,
    task_output: dict,
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a knowledge engineer. Distill the following successful task "
                "into a concise, reusable SOP skill document in Markdown. "
                "Structure: # Title, ## When to use, ## Prerequisites, ## Steps, "
                "## Watch-outs, ## Example output."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Role: {agent_role}\n"
                f"Task type: {task_type}\n"
                f"Input: {task_input}\n"
                f"Output: {task_output}\n\n"
                "Write the Markdown SOP:"
            ),
        },
    ]
    try:
        text, _ = await complete_chat(messages, temperature=0.3)
        return text
    except Exception:
        return ""


def _extract_title(md: str) -> str:
    for line in md.splitlines():
        stripped = line.lstrip("# ").strip()
        if stripped:
            return stripped[:120]
    return "Skill Document"
