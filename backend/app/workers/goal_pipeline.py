"""Sequential multi-role execution: one business goal, hunter → researcher → outreach → delivery."""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from app.agents.base_agent import TaskStub
from app.agents.delivery_agent import DeliveryAgent
from app.agents.hunter_agent import HunterAgent
from app.agents.outreach_agent import OutreachAgent
from app.agents.researcher_agent import ResearcherAgent
from app.models.domain import Agent, Task


async def run_goal_pipeline(
    *,
    db,
    task: Task,
    coordinator_agent: Agent,
) -> tuple[dict[str, Any], int, bool, str | None]:
    """Run default GTM chain using the tenant's active agents (one per role).

    Returns ``(output, total_tokens, success, error_message)``.
    """
    inp = task.input or {}
    goal = (inp.get("goal") or inp.get("criteria") or "").strip() or str(inp)

    res = await db.execute(
        select(Agent)
        .where(Agent.tenant_id == task.tenant_id)
        .where(Agent.status == "active")
    )
    agents_list = list(res.scalars().all())
    by_role: dict[str, Agent] = {}
    for a in agents_list:
        if a.role not in by_role:
            by_role[a.role] = a

    stages: list[dict[str, Any]] = []
    total_tokens = 0
    leads_out: dict[str, Any] = {}
    brief_out: dict[str, Any] = {}
    email_out: dict[str, Any] = {}
    report_md: str | None = None

    tid = str(task.tenant_id)
    tid_task = str(task.id)

    def _stub(task_type: str, input_body: dict) -> TaskStub:
        return TaskStub(id=tid_task, type=task_type, input=input_body)

    # ── 1. Hunter (线索) ──────────────────────────────────────────────────
    if "hunter" in by_role:
        ag = by_role["hunter"]
        hunter = HunterAgent(str(ag.id), tid, ag.current_prompt)
        try:
            r = await hunter.run(_stub("lead_search", {"criteria": goal, "goal": goal}))
            leads_out = r.output or {}
            stages.append(
                {"role": "hunter", "task_type": "lead_search", "output": leads_out, "tokens": r.token_used}
            )
            total_tokens += r.token_used
        except Exception as exc:
            return {"stages": stages, "error": str(exc)}, total_tokens, False, str(exc)
    else:
        stages.append({"role": "hunter", "skipped": True, "reason": "no_active_agent"})

    leads = leads_out.get("leads") if isinstance(leads_out, dict) else None
    company = goal
    if isinstance(leads, list) and leads and isinstance(leads[0], dict):
        company = (
            leads[0].get("company_name")
            or leads[0].get("company")
            or company
        )

    # ── 2. Researcher (调研) ────────────────────────────────────────────────
    if "researcher" in by_role:
        ag = by_role["researcher"]
        rch = ResearcherAgent(str(ag.id), tid, ag.current_prompt)
        ctx = json.dumps(leads_out, ensure_ascii=False)[:2400]
        try:
            r = await rch.run(
                _stub(
                    "company_research",
                    {
                        "company_name": company,
                        "company": company,
                        "context": f"Business goal: {goal}\nUpstream lead stage output:\n{ctx}",
                    },
                )
            )
            brief_out = r.output or {}
            stages.append(
                {
                    "role": "researcher",
                    "task_type": "company_research",
                    "output": brief_out,
                    "tokens": r.token_used,
                }
            )
            total_tokens += r.token_used
        except Exception as exc:
            return {"stages": stages, "error": str(exc)}, total_tokens, False, str(exc)
    else:
        stages.append({"role": "researcher", "skipped": True, "reason": "no_active_agent"})

    # ── 3. Outreach (触达草稿) ─────────────────────────────────────────────
    if "outreach" in by_role:
        ag = by_role["outreach"]
        out = OutreachAgent(str(ag.id), tid, ag.current_prompt)
        contact, comp_name, to_email = "", company, ""
        if isinstance(leads, list) and leads and isinstance(leads[0], dict):
            d0 = leads[0]
            contact = str(d0.get("contact_name", "") or "")
            comp_name = str(d0.get("company_name", comp_name) or comp_name)
            to_email = str(d0.get("email", "") or "")
        brief_txt = json.dumps(brief_out, ensure_ascii=False)[:4000]
        try:
            r = await out.run(
                _stub(
                    "email_write",
                    {
                        "contact_name": contact or "there",
                        "company_name": comp_name,
                        "email": to_email,
                        "context": f"Goal: {goal}\nResearch:\n{brief_txt}",
                    },
                )
            )
            email_out = r.output or {}
            stages.append(
                {"role": "outreach", "task_type": "email_write", "output": email_out, "tokens": r.token_used}
            )
            total_tokens += r.token_used
        except Exception as exc:
            return {"stages": stages, "error": str(exc)}, total_tokens, False, str(exc)
    else:
        stages.append({"role": "outreach", "skipped": True, "reason": "no_active_agent"})

    # ── 4. Delivery (汇总交付) ─────────────────────────────────────────────
    if "delivery" in by_role:
        ag = by_role["delivery"]
        deliv = DeliveryAgent(str(ag.id), tid, ag.current_prompt)
        bundle = {"goal": goal, "leads": leads_out, "research": brief_out, "outreach": email_out}
        try:
            r = await deliv.run(
                _stub("deal_summary", {"content": json.dumps(bundle, ensure_ascii=False)})
            )
            dout = r.output or {}
            report_md = dout.get("report_md") if isinstance(dout, dict) else None
            stages.append(
                {"role": "delivery", "task_type": "deal_summary", "output": dout, "tokens": r.token_used}
            )
            total_tokens += r.token_used
        except Exception as exc:
            return {"stages": stages, "error": str(exc)}, total_tokens, False, str(exc)
    else:
        stages.append({"role": "delivery", "skipped": True, "reason": "no_active_agent"})

    ran_any = any("tokens" in s for s in stages)
    if not ran_any:
        return (
            {"stages": stages, "error": "No pipeline agents (hunter/researcher/outreach/delivery) are active."},
            0,
            False,
            "no_pipeline_agents",
        )

    out: dict[str, Any] = {
        "collaborative": True,
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
