"""LLM-driven routing for smart launch — task type, workflow template, coordinator role."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from app.agents.discipline_harness import intent_gate_heuristic
from app.industry_plugins import get_plugin
from app.models.domain import Tenant
from app.services.llm import complete_chat
from app.services.task_smart_routing import VALID_SMART_TASK_TYPES, infer_task_type_from_goal


@dataclass
class SmartLaunchPlan:
    task_type: str
    workflow_index: Optional[int] = None
    workflow_name: Optional[str] = None
    coordinator_role: Optional[str] = None
    reasoning: str = ""
    true_intent: str = ""
    success_criteria: str = ""


def _first_node_role(nodes: Any) -> Optional[str]:
    if not isinstance(nodes, list):
        return None
    for n in nodes:
        if isinstance(n, dict) and n.get("role"):
            return str(n["role"])
    return None


async def plan_smart_launch(
    *,
    goal: str,
    tenant: Tenant,
    user_workflow_index: Optional[int] = None,
    user_workflow_name: Optional[str] = None,
) -> SmartLaunchPlan:
    """Use the configured LLM to pick execution mode; respect explicit workflow hints from the client."""
    goal = goal.strip()
    intent = intent_gate_heuristic(goal)
    if user_workflow_name and user_workflow_name.strip():
        return SmartLaunchPlan(
            task_type="goal_pipeline",
            workflow_name=user_workflow_name.strip(),
            coordinator_role="manager",
            reasoning="Client specified workflow name — collaborative pipeline.",
            true_intent=intent["true_intent"],
            success_criteria=intent["success_criteria"],
        )
    if user_workflow_index is not None:
        return SmartLaunchPlan(
            task_type="goal_pipeline",
            workflow_index=int(user_workflow_index),
            coordinator_role="manager",
            reasoning="Client specified workflow index — collaborative pipeline.",
            true_intent=intent["true_intent"],
            success_criteria=intent["success_criteria"],
        )

    plugin = get_plugin(tenant.industry_plugin)
    templates = plugin.get_workflow_templates() if plugin else []
    lines: list[str] = []
    for i, t in enumerate(templates):
        dag = t.dag_config or {}
        nodes = dag.get("nodes", [])
        rlist = [str(n.get("role")) for n in nodes if isinstance(n, dict) and n.get("role")]
        lines.append(f"{i}: {t.name} → roles: {', '.join(rlist)}")
    catalog = "\n".join(lines) if lines else "(no workflow templates in this industry plugin)"
    allowed = ", ".join(sorted(VALID_SMART_TASK_TYPES))

    system = (
        "You are the Titan OS smart router. Read the user business goal (any language) "
        "and choose how to execute it.\n"
        "Reply with JSON ONLY, keys:\n"
        "- task_type: one of the allowed literal strings.\n"
        "- workflow_index: integer 0..N-1 if task_type is goal_pipeline, else null.\n"
        "- workflow_name: short substring to match a template name, or null (prefer index).\n"
        "- coordinator_role: role id of the first executor in the chosen workflow "
        "(e.g. manager, hunter, strategy_director) — must exist as a key in the template nodes.\n"
        "- reasoning: one concise sentence.\n\n"
        "Rules:\n"
        "- Prefer goal_pipeline when the user wants multiple steps, end-to-end delivery, "
        "cross-functional collaboration, or the goal is broad/ambiguous.\n"
        "- Prefer parallel_team when the user wants multiple agents working in parallel "
        "(simultaneous research + outreach, parallel sub-tasks, team mode).\n"
        "- Prefer a single task_type only when the request is clearly one atomic deliverable.\n"
        "- Pick workflow_index by semantic fit with the goal.\n"
        f"Allowed task_type values: {allowed}.\n"
    )
    user = (
        f"User goal:\n{goal[:7000]}\n\n"
        f"Intent gate (pre-analysis):\n"
        f"- true_intent: {intent['true_intent']}\n"
        f"- success_criteria: {intent['success_criteria']}\n\n"
        f"Industry workflow templates:\n{catalog}\n"
    )

    try:
        text, _ = await complete_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.15,
        )
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            raise ValueError("no json")
        data = json.loads(m.group())
        if not isinstance(data, dict):
            raise ValueError("bad shape")
        tt = str(data.get("task_type", "")).strip()
        if tt not in VALID_SMART_TASK_TYPES:
            raise ValueError("bad task_type")
        wi_raw = data.get("workflow_index")
        wi: Optional[int] = None
        if wi_raw is not None:
            try:
                wi = int(wi_raw)
            except (TypeError, ValueError):
                wi = None
        wn = data.get("workflow_name")
        wn_s = str(wn).strip() if isinstance(wn, str) and str(wn).strip() else None
        cr = data.get("coordinator_role")
        cr_s = str(cr).strip() if isinstance(cr, str) and str(cr).strip() else None
        reason = str(data.get("reasoning", "")).strip() or "Model routing"
        if tt == "goal_pipeline" and templates:
            if wi is None and wn_s is None:
                wi = 0
            if wi is not None:
                wi = max(0, min(wi, len(templates) - 1))
            if not cr_s and wi is not None:
                dag = templates[wi].dag_config or {}
                cr_s = _first_node_role(dag.get("nodes", []))
            elif not cr_s and wn_s:
                for t in templates:
                    if wn_s.lower() in t.name.lower():
                        dag = t.dag_config or {}
                        cr_s = _first_node_role(dag.get("nodes", []))
                        break
        return SmartLaunchPlan(
            task_type=tt,
            workflow_index=wi,
            workflow_name=wn_s,
            coordinator_role=cr_s,
            reasoning=reason,
            true_intent=intent["true_intent"],
            success_criteria=intent["success_criteria"],
        )
    except Exception:
        fb = infer_task_type_from_goal(goal)
        if fb == "goal_pipeline" and templates:
            cr = _first_node_role((templates[0].dag_config or {}).get("nodes", [])) or "manager"
            return SmartLaunchPlan(
                task_type="goal_pipeline",
                workflow_index=0,
                coordinator_role=cr,
                reasoning="Fallback: keyword router selected collaborative pipeline.",
                true_intent=intent["true_intent"],
                success_criteria=intent["success_criteria"],
            )
        return SmartLaunchPlan(
            task_type=fb,
            reasoning="Fallback: keyword router.",
            true_intent=intent["true_intent"],
            success_criteria=intent["success_criteria"],
        )
