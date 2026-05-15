"""Management agent: interpret skipped pipeline stages and spawn focused child tasks."""
from __future__ import annotations

import json
import re
from typing import Any

from app.models.domain import Agent, Task
from app.services.llm import complete_chat
from app.services.task_smart_routing import VALID_SMART_TASK_TYPES, pick_agent_for_task
from app.workers.pipeline_followup import MANAGER_SKILL_CLOSURE

# Single-step tasks only — no nested pipelines from closure.
_SPAWNABLE = frozenset(VALID_SMART_TASK_TYPES - {"goal_pipeline", MANAGER_SKILL_CLOSURE})

_MAX_CHILDREN = 5


def _extract_json_object(text: str) -> dict[str, Any] | None:
    try:
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        return json.loads(m.group())
    except Exception:
        return None


async def run_skill_gap_closure(
    *,
    db,
    task: Task,
    manager: Agent,
) -> tuple[dict[str, Any], int, bool, str | None]:
    """LLM proposes remediation tasks; we create pending Task rows and enqueue Celery for each."""
    inp = task.input or {}
    parent_id = inp.get("parent_task_id")
    goal = str(inp.get("goal") or "")
    workflow = inp.get("workflow")
    skipped = inp.get("skipped_stages") or []
    stages = inp.get("stages") or []

    skipped_txt = json.dumps(skipped, ensure_ascii=False)[:4000]
    stages_txt = json.dumps(stages, ensure_ascii=False)[:6000]

    system = (
        "You are an Evolution Manager. A collaborative business pipeline (goal_pipeline) finished but "
        "some DAG stages were SKIPPED because no active digital employee existed for that role.\n"
        "Your job: propose up to "
        f"{_MAX_CHILDREN} focused follow-up tasks so the organisation can still progress. Each task must be "
        "ONE atomic step assignable to a single agent role.\n"
        "Return JSON only with this shape:\n"
        '{"assessment":"short text","child_tasks":['
        '{"task_type":"<literal>","goal":"<concrete sub-goal tied to the main goal>","rationale":"<why>"}'
        "]}\n"
        f"Allowed task_type literals: {', '.join(sorted(_SPAWNABLE))}.\n"
        "Do NOT use goal_pipeline. Goals must be self-contained (include necessary context / geography / segment)."
    )
    user = (
        f"Main goal: {goal}\n"
        f"Workflow name: {workflow}\n"
        f"Skipped stages: {skipped_txt}\n"
        f"Full stage log (truncated): {stages_txt}\n"
    )

    text, tokens = await complete_chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.15,
    )

    parsed = _extract_json_object(text) or {}
    assessment = str(parsed.get("assessment") or text[:800])
    raw_children = parsed.get("child_tasks")
    if not isinstance(raw_children, list):
        raw_children = []

    spawned: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    from app.core.plan_limits import check_task_limit
    from app.models.domain import Tenant

    tenant_row = await db.get(Tenant, task.tenant_id)
    plan = tenant_row.plan if tenant_row else "starter"

    for item in raw_children[:_MAX_CHILDREN]:
        if not isinstance(item, dict):
            continue
        tt = str(item.get("task_type") or "").strip()
        sub_goal = str(item.get("goal") or "").strip()
        if tt not in _SPAWNABLE or len(sub_goal) < 8:
            rejected.append({"item": item, "reason": "invalid_type_or_goal"})
            continue

        ok_limit, limit_msg = await check_task_limit(str(task.tenant_id), plan, db)
        if not ok_limit:
            rejected.append({"item": item, "reason": limit_msg})
            break

        exec_agent = await pick_agent_for_task(db, task.tenant_id, tt)
        if exec_agent is None:
            rejected.append({"item": item, "reason": "no_active_agent"})
            continue

        child = Task(
            tenant_id=task.tenant_id,
            agent_id=exec_agent.id,
            task_type=tt,
            input={
                "goal": sub_goal,
                "criteria": sub_goal,
                "parent_task_id": str(parent_id) if parent_id else None,
                "spawned_by_closure_task_id": str(task.id),
                "closure_rationale": str(item.get("rationale") or ""),
            },
        )
        db.add(child)
        await db.flush()
        spawned.append(
            {
                "task_id": str(child.id),
                "task_type": tt,
                "agent_id": str(exec_agent.id),
                "agent_name": exec_agent.name,
                "goal": sub_goal,
            }
        )

    out: dict[str, Any] = {
        "closure_kind": MANAGER_SKILL_CLOSURE,
        "parent_task_id": parent_id,
        "assessment": assessment,
        "llm_raw_head": text[:1200],
        "child_tasks_spawned": spawned,
        "child_tasks_rejected": rejected,
    }
    # LLM proposed children but none could be created (limits / no agent / invalid types).
    err: str | None = None
    if raw_children and not spawned:
        err = "no_child_tasks_spawned"
    success = err is None
    return out, tokens, success, err
