"""Evolution worker — periodic task that scans all agents and triggers evolution."""
from __future__ import annotations

import asyncio

from app.workers.celery_app import celery_app


@celery_app.task(name="titan.evolution.scan_all")
def scan_all_agents() -> dict:
    """Scan every active agent; evolve those that are below threshold."""
    return asyncio.get_event_loop().run_until_complete(_scan())


async def _scan() -> dict:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.evolution.ab_test import create_ab_test
    from app.evolution.evolver import maybe_evolve
    from app.evolution.scorer import compute_agent_stats
    from app.models.domain import Agent

    evolved: list[str] = []
    skipped: list[str] = []

    async with AsyncSessionLocal() as db:
        agents_q = await db.execute(
            select(Agent).where(Agent.status == "active")
        )
        agents = agents_q.scalars().all()

        for agent in agents:
            stats = await compute_agent_stats(agent.id, db)
            if not stats.below_threshold:
                skipped.append(str(agent.id))
                continue

            new_pv = await maybe_evolve(agent, stats, db)
            if new_pv:
                await create_ab_test(agent, new_pv, db)
                evolved.append(str(agent.id))

    return {"evolved": evolved, "skipped": len(skipped)}


@celery_app.task(name="titan.evolution.evolve_agent")
def evolve_agent(agent_id: str) -> dict:
    """Manually trigger evolution for a specific agent."""
    return asyncio.get_event_loop().run_until_complete(_evolve_one(agent_id))


async def _evolve_one(agent_id: str) -> dict:
    import uuid

    from app.core.database import AsyncSessionLocal
    from app.evolution.ab_test import create_ab_test
    from app.evolution.evolver import maybe_evolve
    from app.evolution.scorer import compute_agent_stats
    from app.models.domain import Agent

    async with AsyncSessionLocal() as db:
        agent = await db.get(Agent, uuid.UUID(agent_id))
        if agent is None:
            return {"error": "agent not found"}
        stats = await compute_agent_stats(agent.id, db)
        new_pv = await maybe_evolve(agent, stats, db)
        if new_pv is None:
            return {"evolved": False, "reason": "threshold not met or already testing"}
        test = await create_ab_test(agent, new_pv, db)
        return {
            "evolved": True,
            "new_version": new_pv.version,
            "ab_test_id": str(test.id),
            "kpi_score": stats.kpi_score,
        }
