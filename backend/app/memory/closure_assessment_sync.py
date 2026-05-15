"""Persist closure assessments to PerformanceLog.extra and SkillDoc (evolution loop)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Agent, SkillDoc, Task

# One rolling ledger per tenant — appended markdown + structured meta.closure_events
_GAP_LEDGER_NAME = "【系统】缺口闭环流水账"
_MAX_LEDGER_CHARS = 120_000


def build_performance_log_extra(
    *,
    task: Task,
    agent: Agent,
    task_type: str,
    result_output: dict[str, Any],
    success: bool,
) -> dict[str, Any]:
    """Structured audit payload for KPI / A-B proxies / closure tracing."""
    extra: dict[str, Any] = {
        "task_type": task_type,
        "agent_role": agent.role,
        "prompt_version": agent.prompt_version,
        "agent_status_at_run": agent.status,
        "ab_testing_active": agent.status == "testing",
        "auto_success": success,
    }
    if agent.status == "testing":
        # Deterministic stratum until runners attach real variant id to Task.input
        h = hash((str(task.id), str(agent.id)))
        extra["ab_proxy_variant"] = "a" if (h % 2) == 0 else "b"

    if task_type == MANAGER_SKILL_CLOSURE:
        inp = task.input or {}
        parent = result_output.get("parent_task_id") or inp.get("parent_task_id")
        spawned = result_output.get("child_tasks_spawned")
        rejected = result_output.get("child_tasks_rejected")
        n_spawn = len(spawned) if isinstance(spawned, list) else 0
        n_rej = len(rejected) if isinstance(rejected, list) else 0
        extra["closure"] = {
            "parent_task_id": str(parent) if parent else None,
            "assessment": str(result_output.get("assessment") or "")[:8000],
            "child_tasks_spawned_count": n_spawn,
            "child_tasks_rejected_count": n_rej,
        }
    return extra


async def upsert_gap_closure_skill_ledger(
    db: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    manager_agent: Agent,
    task: Task,
    result_output: dict[str, Any],
    success: bool,
) -> SkillDoc | None:
    """Append manager closure assessment to a tenant-wide SkillDoc for retrieval & light success_rate drift."""
    assessment = str(result_output.get("assessment") or "").strip()
    if not assessment:
        return None

    stamp = datetime.now(timezone.utc).isoformat()
    block = (
        f"\n\n## {stamp} · task `{task.id}` · {manager_agent.name} ({manager_agent.role})\n\n"
        f"{assessment[:6000]}\n"
    )
    spawned = result_output.get("child_tasks_spawned")
    if isinstance(spawned, list) and spawned:
        parts = []
        for x in spawned[:12]:
            if isinstance(x, dict):
                parts.append(f"{x.get('task_type', '?')} → `{x.get('task_id', '')}`")
        if parts:
            block += "\n**Spawned:** " + " · ".join(parts) + "\n"

    res = await db.execute(
        select(SkillDoc).where(SkillDoc.tenant_id == tenant_id).where(SkillDoc.name == _GAP_LEDGER_NAME).limit(1)
    )
    row = res.scalars().first()
    tags = ["manager", "gap_closure", manager_agent.role]
    tags = list(dict.fromkeys(tags))

    bump = 0.88 if success and (spawned and isinstance(spawned, list) and len(spawned) > 0) else (0.72 if success else 0.38)

    if row is None:
        skill = SkillDoc(
            tenant_id=tenant_id,
            name=_GAP_LEDGER_NAME,
            description="管理层缺口闭环任务写入的评估摘要，供技能检索、复盘与进化数据聚合。",
            content_md=f"# {_GAP_LEDGER_NAME}\n{block}",
            role_tags=tags,
            industry_tags=[],
            source_agent_id=manager_agent.id,
            usage_count=1,
            success_rate=bump,
            meta={
                "kind": "gap_closure_ledger",
                "closure_events": [{"task_id": str(task.id), "at": stamp, "success": success}],
            },
        )
        db.add(skill)
        await db.flush()
        return skill

    row.content_md = (row.content_md or "") + block
    if len(row.content_md) > _MAX_LEDGER_CHARS:
        row.content_md = row.content_md[-_MAX_LEDGER_CHARS:]
    row.usage_count = int(row.usage_count or 0) + 1
    prev = float(row.success_rate or 0.0)
    row.success_rate = min(0.99, prev * 0.92 + bump * 0.08)
    md = dict(row.meta) if isinstance(row.meta, dict) else {}
    ev = list(md.get("closure_events") or [])
    ev.append({"task_id": str(task.id), "at": stamp, "success": success})
    md["closure_events"] = ev[-80:]
    md["kind"] = "gap_closure_ledger"
    row.meta = md
    if not row.description:
        row.description = "管理层缺口闭环任务写入的评估摘要，供技能检索、复盘与进化数据聚合。"
    await db.flush()
    return row
