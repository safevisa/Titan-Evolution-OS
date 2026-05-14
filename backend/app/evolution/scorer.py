"""KPI scoring engine — computes an agent's current performance score.

Score formula (from spec):
  base = 0.50 × success_rate + 0.30 × avg_quality_score - 0.20 × token_norm
  token_norm = agent_avg_tokens / baseline_tokens  (capped at 1)
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import PerformanceLog, Task

_BASELINE_TOKENS = 2000.0
_EVOLUTION_THRESHOLD = 0.65
_MIN_SAMPLES = 20


@dataclass
class AgentStats:
    agent_id: uuid.UUID
    sample_count: int
    success_rate: float
    avg_quality_score: float
    avg_tokens: float
    kpi_score: float
    below_threshold: bool


async def compute_agent_stats(agent_id: uuid.UUID, db: AsyncSession) -> AgentStats:
    """Aggregate last 100 performance logs for the given agent."""
    rows = await db.execute(
        select(PerformanceLog)
        .where(PerformanceLog.agent_id == agent_id)
        .order_by(PerformanceLog.created_at.desc())
        .limit(100)
    )
    logs = list(rows.scalars().all())
    n = len(logs)
    if n == 0:
        return AgentStats(agent_id=agent_id, sample_count=0, success_rate=0.0,
                          avg_quality_score=0.0, avg_tokens=0.0, kpi_score=0.0,
                          below_threshold=False)

    successes = sum(1 for l in logs if l.success_flag)
    success_rate = successes / n

    quality_scores = [l.quality_score for l in logs if l.quality_score is not None]
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5

    avg_tokens = sum(l.token_cost for l in logs) / n
    token_norm = min(avg_tokens / _BASELINE_TOKENS, 1.0)

    kpi = 0.50 * success_rate + 0.30 * avg_quality - 0.20 * token_norm
    kpi = max(0.0, min(1.0, kpi))

    return AgentStats(
        agent_id=agent_id,
        sample_count=n,
        success_rate=round(success_rate, 3),
        avg_quality_score=round(avg_quality, 3),
        avg_tokens=round(avg_tokens, 1),
        kpi_score=round(kpi, 3),
        below_threshold=(n >= _MIN_SAMPLES and kpi < _EVOLUTION_THRESHOLD),
    )


async def get_failure_cases(agent_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
    """Return recent failed tasks with their inputs/outputs for the evolver."""
    rows = await db.execute(
        select(Task, PerformanceLog)
        .join(PerformanceLog, PerformanceLog.task_id == Task.id)
        .where(Task.agent_id == agent_id)
        .where(PerformanceLog.success_flag == False)  # noqa: E712
        .order_by(PerformanceLog.created_at.desc())
        .limit(limit)
    )
    results = []
    for task, perf in rows.all():
        results.append({
            "task_type": task.task_type,
            "input": task.input,
            "output": task.output,
            "quality_score": perf.quality_score,
            "auto_eval_reason": perf.auto_eval_reason,
            "human_feedback": perf.human_feedback,
        })
    return results
