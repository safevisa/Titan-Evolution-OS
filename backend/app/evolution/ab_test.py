"""A/B test management — create tests, route tasks, conclude with a winner.

Performance correlation: worker writes ``PerformanceLog.extra`` with
``prompt_version``, ``ab_testing_active``, and ``ab_proxy_variant`` (deterministic
stratum while ``agent.status == \"testing\"``) for downstream analytics.
"""
from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import ABTest, Agent, PerformanceLog, PromptVersion


async def create_ab_test(
    agent: Agent,
    candidate_version: PromptVersion,
    db: AsyncSession,
) -> ABTest:
    """Create an A/B test between the current active prompt and a new candidate."""
    # Ensure current version exists in prompt_versions
    current_pv_q = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.agent_id == agent.id)
        .where(PromptVersion.status == "active")
        .order_by(PromptVersion.version.desc())
        .limit(1)
    )
    current_pv = current_pv_q.scalars().first()
    if current_pv is None:
        # Bootstrap: create a version record for the current prompt
        current_pv = PromptVersion(
            agent_id=agent.id,
            version=agent.prompt_version,
            content=agent.current_prompt,
            status="active",
            evolved_reason="Bootstrapped from agent current_prompt",
        )
        db.add(current_pv)
        await db.flush()

    test = ABTest(
        agent_id=agent.id,
        variant_a_id=current_pv.id,
        variant_b_id=candidate_version.id,
        status="running",
    )
    db.add(test)
    # Mark agent as testing
    agent.status = "testing"
    await db.commit()
    await db.refresh(test)
    return test


async def get_prompt_for_task(agent: Agent, db: AsyncSession) -> str:
    """50/50 routing: return variant B prompt if an A/B test is running."""
    if agent.status != "testing":
        return agent.current_prompt

    test_q = await db.execute(
        select(ABTest)
        .where(ABTest.agent_id == agent.id)
        .where(ABTest.status == "running")
        .order_by(ABTest.started_at.desc())
        .limit(1)
    )
    test = test_q.scalars().first()
    if test is None:
        return agent.current_prompt

    if random.random() < 0.5:
        pv = await db.get(PromptVersion, test.variant_b_id)
        return pv.content if pv else agent.current_prompt
    return agent.current_prompt


async def conclude_ab_test(
    test_id: uuid.UUID,
    db: AsyncSession,
    force_winner: str | None = None,  # "a" | "b" | None (auto)
) -> ABTest:
    """Evaluate results and promote the winner prompt to the agent."""
    test = await db.get(ABTest, test_id)
    if test is None:
        raise ValueError(f"ABTest {test_id} not found")
    if test.status != "running":
        raise ValueError(f"ABTest {test_id} is not running")

    # Compute per-variant success rates from performance logs
    async def _score(pv_id: uuid.UUID) -> float:
        pv = await db.get(PromptVersion, pv_id)
        if pv is None:
            return 0.0
        logs_q = await db.execute(
            select(PerformanceLog)
            .where(PerformanceLog.agent_id == test.agent_id)
            .order_by(PerformanceLog.created_at.desc())
            .limit(40)
        )
        logs = logs_q.scalars().all()
        if not logs:
            return 0.0
        successes = sum(1 for l in logs if l.success_flag)
        qs = [l.quality_score for l in logs if l.quality_score is not None]
        avg_q = sum(qs) / len(qs) if qs else 0.5
        return 0.5 * (successes / len(logs)) + 0.5 * avg_q

    score_a = await _score(test.variant_a_id)
    score_b = await _score(test.variant_b_id)

    if force_winner == "a":
        winner_id = test.variant_a_id
    elif force_winner == "b":
        winner_id = test.variant_b_id
    else:
        winner_id = test.variant_b_id if score_b >= score_a else test.variant_a_id

    # Promote winner to agent
    agent = await db.get(Agent, test.agent_id)
    winner_pv = await db.get(PromptVersion, winner_id)
    if agent and winner_pv:
        agent.current_prompt = winner_pv.content
        agent.prompt_version = winner_pv.version
        agent.status = "active"
        winner_pv.status = "active"
        winner_pv.avg_score = score_b if winner_id == test.variant_b_id else score_a

    # Archive the loser
    loser_id = test.variant_a_id if winner_id == test.variant_b_id else test.variant_b_id
    loser_pv = await db.get(PromptVersion, loser_id)
    if loser_pv:
        loser_pv.status = "archived"

    test.winner_id = winner_id
    test.status = "concluded"
    test.ended_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(test)
    return test
