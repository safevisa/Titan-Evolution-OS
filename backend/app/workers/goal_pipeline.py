"""Multi-step business goals: coordinator (manager) runs the tenant industry workflow DAG."""
from __future__ import annotations

import json
from collections import deque
from typing import Any

from sqlalchemy import select

from app.agents.base_agent import BaseAgent, TaskStub
from app.agents.delivery_agent import DeliveryAgent
from app.agents.generic_role_agent import GenericRoleAgent
from app.agents.hunter_agent import HunterAgent
from app.agents.manager_agent import ManagerAgent
from app.agents.outreach_agent import OutreachAgent
from app.agents.researcher_agent import ResearcherAgent
from app.industry_plugins import get_plugin
from app.models.domain import Agent, Task, Tenant


def _topo_ordered_nodes(nodes: list[dict[str, Any]], edges: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Topological order; fallback to declaration order if graph is inconsistent."""
    by_id = {n["id"]: n for n in nodes}
    preds: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    succs: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        f, t = e.get("from"), e.get("to")
        if f in succs and t in preds:
            succs[f].append(t)
            preds[t].append(f)
    q = deque([nid for nid, ps in preds.items() if not ps])
    out: list[dict[str, Any]] = []
    pred_copy = {k: list(v) for k, v in preds.items()}
    while q:
        nid = q.popleft()
        out.append(by_id[nid])
        for s in succs.get(nid, []):
            if s in pred_copy and nid in pred_copy[s]:
                pred_copy[s].remove(nid)
            if s in pred_copy and not pred_copy[s]:
                q.append(s)
    if len(out) != len(nodes):
        return list(nodes)
    return out


def resolve_workflow_dag(
    plugin_id: str,
    task_input: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]], str, int]:
    """Pick DAG from plugin templates using ``workflow_index`` or substring ``workflow_name``."""
    task_input = task_input or {}
    plugin = get_plugin(plugin_id)
    templates = plugin.get_workflow_templates() if plugin else []

    def _fallback() -> tuple[list[dict[str, Any]], list[dict[str, str]], str, int]:
        nodes = [
            {"id": "hunt", "role": "hunter", "task_type": "lead_search"},
            {"id": "research", "role": "researcher", "task_type": "company_research"},
            {"id": "outreach", "role": "outreach", "task_type": "email_write"},
            {"id": "deliver", "role": "delivery", "task_type": "deal_summary"},
        ]
        edges = [
            {"from": "hunt", "to": "research"},
            {"from": "research", "to": "outreach"},
            {"from": "outreach", "to": "deliver"},
        ]
        return nodes, edges, "default_gtm_fallback", -1

    if not templates:
        return _fallback()

    name_q = task_input.get("workflow_name")
    chosen_i = 0
    if isinstance(name_q, str) and name_q.strip():
        needle = name_q.strip().lower()
        for i, t in enumerate(templates):
            if needle in t.name.lower():
                chosen_i = i
                break
    else:
        wi = task_input.get("workflow_index", 0)
        try:
            chosen_i = int(wi)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            chosen_i = 0
        chosen_i = max(0, min(chosen_i, len(templates) - 1))

    tmpl = templates[chosen_i]
    dag = tmpl.dag_config or {}
    nodes = list(dag.get("nodes", []))
    edges = list(dag.get("edges", []))
    if not nodes:
        return _fallback()
    return nodes, edges, tmpl.name, chosen_i


def _make_runner(agent: Agent) -> BaseAgent:
    tid = str(agent.tenant_id)
    aid = str(agent.id)
    prompt = agent.current_prompt or ""
    if agent.role == "hunter":
        return HunterAgent(aid, tid, prompt)
    if agent.role == "researcher":
        return ResearcherAgent(aid, tid, prompt)
    if agent.role == "outreach":
        return OutreachAgent(aid, tid, prompt)
    if agent.role == "delivery":
        return DeliveryAgent(aid, tid, prompt)
    if agent.role == "manager":
        return ManagerAgent(aid, tid, prompt)
    return GenericRoleAgent(aid, tid, prompt, role_key=agent.role)


def _leads_from_output(out: dict[str, Any] | None) -> list[Any] | None:
    if not isinstance(out, dict):
        return None
    leads = out.get("leads")
    return leads if isinstance(leads, list) else None


def _company_from_leads_or_goal(leads: list[Any] | None, goal: str) -> str:
    company = goal
    if leads and isinstance(leads[0], dict):
        d0 = leads[0]
        company = str(d0.get("company_name") or d0.get("company") or company)
    return company


def _build_stage_input(
    *,
    role: str,
    task_type: str,
    goal: str,
    pred_ids: list[str],
    outputs_by_node: dict[str, dict[str, Any]],
    leads_acc: dict[str, Any],
    brief_acc: dict[str, Any],
    email_acc: dict[str, Any],
) -> dict[str, Any]:
    """Compose task.input for GTM-shaped stages and generic corporate roles."""
    leads = _leads_from_output(leads_acc.get("output")) if leads_acc else None
    company = _company_from_leads_or_goal(leads, goal)

    if role == "hunter" and task_type in ("lead_search", "icp_search", "partner_discovery"):
        return {"criteria": goal, "goal": goal}

    if role == "researcher" and task_type in (
        "company_research",
        "tech_stack_research",
        "market_research",
        "competitive_intel",
    ):
        ctx = json.dumps(leads_acc.get("output") or {}, ensure_ascii=False)[:2400]
        return {
            "company_name": company,
            "company": company,
            "context": f"Business goal: {goal}\nUpstream lead stage output:\n{ctx}",
        }

    if role == "outreach" and task_type in ("email_write", "trial_invite", "follow_up_email"):
        contact, comp_name, to_email = "", company, ""
        if leads and isinstance(leads[0], dict):
            d0 = leads[0]
            contact = str(d0.get("contact_name", "") or "")
            comp_name = str(d0.get("company_name", comp_name) or comp_name)
            to_email = str(d0.get("email", "") or "")
        brief_txt = json.dumps(brief_acc.get("output") or {}, ensure_ascii=False)[:4000]
        return {
            "contact_name": contact or "there",
            "company_name": comp_name,
            "email": to_email,
            "context": f"Goal: {goal}\nResearch:\n{brief_txt}",
        }

    if role == "delivery" and task_type in ("deal_summary", "sales_brief", "exec_one_pager"):
        pred_stages = {pid: outputs_by_node.get(pid, {}) for pid in pred_ids}
        bundle = {
            "goal": goal,
            "leads": leads_acc.get("output") or {},
            "research": brief_acc.get("output") or {},
            "outreach": email_acc.get("output") or {},
            "upstream_nodes": pred_stages,
        }
        return {"content": json.dumps(bundle, ensure_ascii=False)}

    if role == "manager" and task_type == "sprint_plan":
        return {"goal": goal}

    upstream = {pid: outputs_by_node.get(pid, {}) for pid in pred_ids}
    return {
        "goal": goal,
        "upstream_stages": upstream,
        "task_hint": task_type,
    }


async def run_goal_pipeline(
    *,
    db,
    task: Task,
    coordinator_agent: Agent,
) -> tuple[dict[str, Any], int, bool, str | None]:
    """Execute the tenant industry's primary workflow DAG; coordinator must be role=manager."""
    inp = task.input or {}
    goal = (inp.get("goal") or inp.get("criteria") or "").strip() or str(inp)

    if coordinator_agent.role != "manager":
        return (
            {
                "error": (
                    "goal_pipeline requires the coordinator to be your Evolution Manager "
                    "(role=manager). That manager then delegates each DAG stage to the "
                    "matching functional digital employee on your team."
                ),
                "coordinator_role": coordinator_agent.role,
            },
            0,
            False,
            "coordinator_must_be_manager",
        )

    tenant: Tenant | None = await db.get(Tenant, task.tenant_id)
    plugin_id = tenant.industry_plugin if tenant else "payment_fintech"
    nodes, edges, wf_name, wf_index = resolve_workflow_dag(plugin_id, inp)
    if not nodes:
        return {"error": "Workflow has no nodes"}, 0, False, "empty_workflow"

    res = await db.execute(
        select(Agent).where(Agent.tenant_id == task.tenant_id).where(Agent.status == "active")
    )
    agents_list = list(res.scalars().all())
    by_role: dict[str, Agent] = {}
    for a in agents_list:
        if a.role not in by_role:
            by_role[a.role] = a

    ordered = _topo_ordered_nodes(nodes, edges)
    stages: list[dict[str, Any]] = []
    total_tokens = 0
    outputs_by_node: dict[str, dict[str, Any]] = {}
    pred_index: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        t = e.get("to")
        f = e.get("from")
        if t in pred_index and f:
            pred_index[t].append(f)

    leads_acc: dict[str, Any] = {}
    brief_acc: dict[str, Any] = {}
    email_acc: dict[str, Any] = {}

    tid_task = str(task.id)

    for node in ordered:
        node_id = node["id"]
        role = str(node.get("role", ""))
        task_type = str(node.get("task_type", "generic"))
        agent = by_role.get(role)
        pred_ids = pred_index.get(node_id, [])

        if agent is None:
            stages.append({"node_id": node_id, "role": role, "skipped": True, "reason": "no_active_agent"})
            continue

        stub_in = _build_stage_input(
            role=role,
            task_type=task_type,
            goal=goal,
            pred_ids=pred_ids,
            outputs_by_node=outputs_by_node,
            leads_acc=leads_acc,
            brief_acc=brief_acc,
            email_acc=email_acc,
        )
        stub = TaskStub(id=tid_task, type=task_type, input=stub_in)
        runner = _make_runner(agent)
        try:
            r = await runner.run(stub)
            entry = {
                "node_id": node_id,
                "role": role,
                "task_type": task_type,
                "agent_id": str(agent.id),
                "agent_name": agent.name,
                "output": r.output,
                "tokens": r.token_used,
            }
            stages.append(entry)
            total_tokens += r.token_used
            outputs_by_node[node_id] = entry
            if role == "hunter":
                leads_acc = entry
            elif role == "researcher":
                brief_acc = entry
            elif role == "outreach":
                email_acc = entry
        except Exception as exc:
            return {"stages": stages, "error": str(exc)}, total_tokens, False, str(exc)

    ran_any = any("tokens" in s for s in stages)
    if not ran_any:
        return (
            {
                "stages": stages,
                "error": "No stages ran — activate agents for each workflow role, or fix the industry workflow.",
            },
            0,
            False,
            "no_stages_ran",
        )

    leads_out = leads_acc.get("output") if leads_acc else {}
    brief_out = brief_acc.get("output") if brief_acc else {}
    email_out = email_acc.get("output") if email_acc else {}
    report_md = None
    last_delivery = next((s for s in reversed(stages) if s.get("role") == "delivery" and "output" in s), None)
    if last_delivery and isinstance(last_delivery.get("output"), dict):
        report_md = last_delivery["output"].get("report_md")

    out: dict[str, Any] = {
        "collaborative": True,
        "workflow": wf_name,
        "workflow_index": wf_index,
        "industry_plugin": plugin_id,
        "coordinator_agent_id": str(coordinator_agent.id),
        "goal": goal,
        "stages": stages,
        "leads": leads_out,
        "research": brief_out,
        "outreach": email_out,
    }
    if report_md is not None:
        out["report_md"] = report_md
    return out, total_tokens, True, None
