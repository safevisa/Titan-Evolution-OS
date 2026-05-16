"""Parallel sub-agent orchestration (omo Team Mode simplified).

Manager (or caller) supplies subtasks; each runs as an independent Celery task.
The parent worker polls children and aggregates results.
"""
from __future__ import annotations

import asyncio
import json
import re
import time
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.models.domain import Agent, Task
from app.services.llm import complete_chat
from app.services.task_smart_routing import VALID_SMART_TASK_TYPES, pick_agent_for_task
from app.workers.pipeline_followup import MANAGER_SKILL_CLOSURE

_SPAWNABLE = frozenset(
    VALID_SMART_TASK_TYPES - {"goal_pipeline", "parallel_team", MANAGER_SKILL_CLOSURE}
)

_MAX_CHILDREN = 8
_DEFAULT_MAX_PARALLEL = 4
_POLL_INTERVAL_SEC = 2.0
_CHILD_TIMEOUT_SEC = 900


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        return json.loads(m.group())
    except Exception:
        return None


async def decompose_goal_into_subtasks(
    *,
    goal: str,
    max_children: int = _MAX_CHILDREN,
) -> tuple[list[dict[str, Any]], int]:
    """LLM splits a goal into parallel single-agent subtasks."""
    system = (
        "You are an Evolution Manager. Break the user's goal into parallel sub-tasks "
        f"(max {max_children}) that different digital employees can run at the same time.\n"
        "Each subtask must be ONE atomic step for a single role.\n"
        "Return JSON only:\n"
        '{"subtasks":[{"role":"hunter|researcher|outreach|delivery|manager|...","task_type":"literal","goal":"..."}]}\n'
        f"Allowed task_type: {', '.join(sorted(_SPAWNABLE))}.\n"
        "Do NOT use goal_pipeline or parallel_team. Goals must be self-contained."
    )
    text, tokens = await complete_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": goal}],
        temperature=0.15,
    )
    parsed = _extract_json_object(text) or {}
    raw = parsed.get("subtasks")
    if not isinstance(raw, list):
        return [], tokens
    out: list[dict[str, Any]] = []
    for item in raw[:max_children]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "").strip()
        tt = str(item.get("task_type") or "").strip()
        sub_goal = str(item.get("goal") or "").strip()
        if role and tt in _SPAWNABLE and len(sub_goal) >= 8:
            out.append({"role": role, "task_type": tt, "goal": sub_goal})
    return out, tokens


async def _wait_for_children(
    *,
    child_ids: list[UUID],
    timeout_sec: float = _CHILD_TIMEOUT_SEC,
) -> list[dict[str, Any]]:
    """Poll child Task rows until all terminal or timeout."""
    from app.core.database import AsyncSessionLocal

    deadline = time.monotonic() + timeout_sec
    terminal = frozenset({"done", "failed"})
    results: list[dict[str, Any]] = []

    while time.monotonic() < deadline:
        all_done = True
        batch: list[dict[str, Any]] = []
        async with AsyncSessionLocal() as db:
            for cid in child_ids:
                row = await db.get(Task, cid)
                if row is None:
                    batch.append({"task_id": str(cid), "status": "missing"})
                    continue
                batch.append(
                    {
                        "task_id": str(row.id),
                        "status": row.status,
                        "task_type": row.task_type,
                        "agent_id": str(row.agent_id),
                        "output": row.output,
                        "token_used": row.token_used,
                        "error": (row.output or {}).get("error") if isinstance(row.output, dict) else None,
                    }
                )
                if row.status not in terminal:
                    all_done = False
        results = batch
        if all_done:
            return results
        await asyncio.sleep(_POLL_INTERVAL_SEC)

    for row in results:
        if row.get("status") not in terminal:
            row["status"] = "timeout"
    return results


async def run_parallel_team(
    *,
    db,
    task: Task,
    coordinator: Agent,
) -> tuple[dict[str, Any], int, bool, str | None]:
    """Spawn parallel child tasks via Celery and aggregate outcomes."""
    inp = task.input or {}
    goal = str(inp.get("goal") or inp.get("criteria") or "").strip()
    subtasks = inp.get("subtasks")
    auto_decompose = inp.get("auto_decompose", True)
    max_parallel = int(inp.get("max_parallel") or _DEFAULT_MAX_PARALLEL)
    max_parallel = max(1, min(max_parallel, _MAX_CHILDREN))

    total_tokens = 0
    specs: list[dict[str, Any]] = []

    if isinstance(subtasks, list) and subtasks:
        for item in subtasks[:_MAX_CHILDREN]:
            if isinstance(item, dict):
                specs.append(item)
    elif auto_decompose and goal:
        specs, decompose_tokens = await decompose_goal_into_subtasks(goal=goal, max_children=max_parallel)
        total_tokens += decompose_tokens

    if not specs:
        return (
            {"error": "no_subtasks", "message": "Provide subtasks[] or enable auto_decompose with a goal."},
            total_tokens,
            False,
            "no_subtasks",
        )

    from app.core.plan_limits import check_task_limit
    from app.models.domain import Tenant

    tenant_row = await db.get(Tenant, task.tenant_id)
    plan = tenant_row.plan if tenant_row else "starter"

    spawned: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    child_ids: list[UUID] = []
    harness_inherit = {
        k: inp[k]
        for k in ("harness_mode", "ultrawork", "computer_use_instruction")
        if k in inp
    }

    for item in specs[:max_parallel]:
        if not isinstance(item, dict):
            continue
        tt = str(item.get("task_type") or "").strip()
        sub_goal = str(item.get("goal") or "").strip()
        role_hint = str(item.get("role") or "").strip() or None

        if tt not in _SPAWNABLE or len(sub_goal) < 8:
            rejected.append({"item": item, "reason": "invalid_type_or_goal"})
            continue

        ok_limit, limit_msg = await check_task_limit(str(task.tenant_id), plan, db)
        if not ok_limit:
            rejected.append({"item": item, "reason": limit_msg})
            break

        exec_agent = await pick_agent_for_task(db, task.tenant_id, tt)
        if exec_agent is None and role_hint:
            res = await db.execute(
                select(Agent)
                .where(Agent.tenant_id == task.tenant_id, Agent.status == "active", Agent.role == role_hint)
                .limit(1)
            )
            exec_agent = res.scalars().first()
        if exec_agent is None:
            rejected.append({"item": item, "reason": "no_active_agent"})
            continue

        child_inp: dict[str, Any] = {
            "goal": sub_goal,
            "criteria": sub_goal,
            "parent_task_id": str(task.id),
            "parallel_team_parent": True,
            **harness_inherit,
        }
        if isinstance(item.get("invoke_capability"), str):
            child_inp["invoke_capability"] = item["invoke_capability"]
        if isinstance(item.get("invoke_capability_params"), dict):
            child_inp["invoke_capability_params"] = item["invoke_capability_params"]

        child = Task(
            tenant_id=task.tenant_id,
            agent_id=exec_agent.id,
            task_type=tt,
            input=child_inp,
        )
        db.add(child)
        await db.flush()
        child_ids.append(child.id)
        spawned.append(
            {
                "task_id": str(child.id),
                "task_type": tt,
                "role": exec_agent.role,
                "agent_id": str(exec_agent.id),
                "agent_name": exec_agent.name,
                "goal": sub_goal,
            }
        )

    if not child_ids:
        return (
            {
                "parallel_team": True,
                "goal": goal,
                "coordinator_agent_id": str(coordinator.id),
                "child_tasks_spawned": [],
                "child_tasks_rejected": rejected,
                "error": "no_child_tasks_spawned",
            },
            total_tokens,
            False,
            "no_child_tasks_spawned",
        )

    await db.commit()

    from app.workers.tasks import enqueue_agent_task

    for cid in child_ids:
        enqueue_agent_task.delay(str(cid))

    child_results = await _wait_for_children(child_ids=child_ids)
    succeeded = sum(1 for r in child_results if r.get("status") == "done")
    failed = len(child_results) - succeeded

    out: dict[str, Any] = {
        "parallel_team": True,
        "goal": goal,
        "coordinator_agent_id": str(coordinator.id),
        "max_parallel": max_parallel,
        "child_tasks_spawned": spawned,
        "child_tasks_rejected": rejected,
        "child_results": child_results,
        "summary": {
            "total": len(child_results),
            "succeeded": succeeded,
            "failed": failed,
        },
    }
    success = failed == 0 and succeeded > 0
    err: str | None = None if success else "partial_or_total_failure"
    if succeeded == 0:
        err = "all_children_failed"
    return out, total_tokens, success, err
