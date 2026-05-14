"""Prompt evolver — analyses failure cases and generates an improved prompt."""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.evolution.scorer import AgentStats, get_failure_cases
from app.models.domain import Agent, PromptVersion
from app.services.llm import complete_chat


async def maybe_evolve(
    agent: Agent,
    stats: AgentStats,
    db: AsyncSession,
) -> PromptVersion | None:
    """
    If the agent is below threshold AND has enough samples, generate a new
    PromptVersion and return it (without activating it — that waits for A/B test).
    """
    if not stats.below_threshold:
        return None

    # Prevent duplicate evolution versions already in testing
    from sqlalchemy import select
    existing = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.agent_id == agent.id)
        .where(PromptVersion.status == "testing")
        .limit(1)
    )
    if existing.scalars().first() is not None:
        return None  # already has a candidate in test

    failures = await get_failure_cases(agent.id, db, limit=10)
    new_content = await _generate_evolved_prompt(
        current_prompt=agent.current_prompt,
        failures=failures,
        stats=stats,
    )
    if not new_content:
        return None

    next_version = (agent.prompt_version or 1) + 1
    pv = PromptVersion(
        agent_id=agent.id,
        version=next_version,
        content=new_content,
        status="testing",
        evolved_reason=(
            f"Auto-evolved from v{agent.prompt_version}: "
            f"kpi={stats.kpi_score:.2f}, samples={stats.sample_count}, "
            f"failures={len(failures)}"
        ),
    )
    db.add(pv)
    await db.commit()
    await db.refresh(pv)
    return pv


async def _generate_evolved_prompt(
    current_prompt: str,
    failures: list[dict],
    stats: AgentStats,
) -> str:
    failure_text = "\n".join(
        f"- type={f['task_type']} score={f.get('quality_score','?')} "
        f"reason={f.get('auto_eval_reason') or f.get('human_feedback','unknown')}"
        for f in failures
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are a Prompt Engineer. Improve the given agent system prompt "
                "based on failure patterns. Rules: keep the core role, address the "
                "failure reasons, do NOT exceed 1.3× the original length, output "
                "ONLY the new prompt text with no explanation."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Current prompt:\n{current_prompt}\n\n"
                f"Recent failures ({len(failures)}):\n{failure_text}\n\n"
                f"Current KPI score: {stats.kpi_score:.2f} "
                f"(success_rate={stats.success_rate:.2f}, "
                f"avg_quality={stats.avg_quality_score:.2f})\n\n"
                "Write the improved prompt:"
            ),
        },
    ]
    try:
        text, _ = await complete_chat(messages, temperature=0.4)
        return text.strip()
    except Exception:
        return ""
