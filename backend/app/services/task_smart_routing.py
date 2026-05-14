"""Infer task type from natural-language goal and pick a coordinating agent."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Agent


def infer_task_type_from_goal(goal: str) -> str:
    """Keyword / phrase routing (zh + en). Defaults to company-wide research."""
    g = (goal or "").strip().lower()

    if any(
        kw in g
        for kw in (
            "全流程",
            "全链路",
            "协作流水线",
            "多步",
            "工作流",
            "端到端",
            "上市流程",
            "从头做到尾",
            "pipeline",
            "gtm",
            "go-to-market",
            "go to market",
        )
    ):
        return "goal_pipeline"

    if any(k in g for k in ("风险评估", "risk assessment", "合规风险", "风险管理")):
        return "risk_assessment"
    if any(k in g for k in ("冲刺计划", "sprint plan", "迭代计划", "sprint 计划")):
        return "sprint_plan"

    if any(k in g for k in ("一页纸", "exec summary", "executive one-pager", "executive one pager")):
        return "exec_one_pager"
    if any(k in g for k in ("销售简报", "sales brief")):
        return "sales_brief"
    if any(k in g for k in ("deal summary", "交易摘要", "订单摘要")):
        return "deal_summary"

    if any(k in g for k in ("试用邀请", "trial invite")):
        return "trial_invite"
    if any(k in g for k in ("跟进邮件", "follow up email", "follow-up email", "follow up")):
        return "follow_up_email"
    if any(k in g for k in ("写邮件", "邮件草稿", "email draft", "cold email", "邮件撰写")):
        return "email_write"

    if any(k in g for k in ("技术栈", "tech stack")):
        return "tech_stack_research"
    if any(k in g for k in ("竞品", "竞争对手", "competitive intel", "competitive")):
        return "competitive_intel"
    if any(k in g for k in ("市场规模", "行业趋势", "market research", "市场研究")):
        return "market_research"
    if any(k in g for k in ("合作伙伴", "渠道伙伴", "partner discovery", "渠道拓展")):
        return "partner_discovery"
    if "icp" in g or "ideal customer" in g or "理想客户" in g:
        return "icp_search"

    if any(
        k in g
        for k in (
            "线索",
            "拓客",
            "潜在客户",
            "名单",
            "lead list",
            "prospecting",
            "prospect list",
        )
    ):
        return "lead_search"

    if any(k in g for k in ("公司调研", "企业背调", "company research", "尽职调查", "背调")):
        return "company_research"

    return "company_research"


def _preferred_roles_for_task(task_type: str) -> list[str]:
    """Order matters: first match wins."""
    if task_type == "goal_pipeline":
        return ["manager", "researcher", "hunter", "outreach", "delivery"]
    if task_type in ("lead_search", "icp_search", "partner_discovery"):
        return ["hunter", "researcher", "manager", "outreach", "delivery"]
    if task_type in (
        "company_research",
        "market_research",
        "competitive_intel",
        "tech_stack_research",
    ):
        return ["researcher", "hunter", "manager", "outreach", "delivery"]
    if task_type in ("email_write", "trial_invite", "follow_up_email"):
        return ["outreach", "researcher", "hunter", "manager", "delivery"]
    if task_type in ("deal_summary", "sales_brief", "exec_one_pager"):
        return ["delivery", "researcher", "outreach", "hunter", "manager"]
    if task_type in ("sprint_plan", "risk_assessment"):
        return ["manager", "researcher", "delivery", "hunter", "outreach"]
    return ["researcher", "hunter", "outreach", "delivery", "manager"]


async def pick_agent_for_task(
    db: AsyncSession,
    tenant_id: UUID,
    task_type: str,
) -> Agent | None:
    res = await db.execute(
        select(Agent)
        .where(Agent.tenant_id == tenant_id, Agent.status == "active")
        .order_by(Agent.created_at.asc())
    )
    agents = list(res.scalars().all())
    if not agents:
        return None
    prefs = _preferred_roles_for_task(task_type)
    for role in prefs:
        for a in agents:
            if a.role == role:
                return a
    return agents[0]
