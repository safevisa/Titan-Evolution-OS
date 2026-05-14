"""SaaS B2B Growth plugin — PLG / outbound for B2B SaaS products."""
from __future__ import annotations

from app.industry_plugins.base_plugin import (
    AgentConfig,
    IndustryPlugin,
    KPIDefinition,
    PluginSkillDoc,
    WorkflowTemplate,
)


class SaasB2BPlugin(IndustryPlugin):

    @property
    def plugin_id(self) -> str:
        return "saas_b2b"

    @property
    def display_name(self) -> str:
        return "SaaS B2B Growth"

    def get_agent_configs(self) -> list[AgentConfig]:
        return [
            AgentConfig(
                role="hunter",
                name="ICP Hunter",
                default_prompt=(
                    "You are an ICP (Ideal Customer Profile) Hunter for a B2B SaaS product. "
                    "Identify companies that fit the ICP: right industry vertical, company size "
                    "(50-500 employees), and have a clear pain point the product solves. "
                    "Target: VP Engineering, Head of Ops, CTO, or Product Lead. "
                    "Return leads as JSON: [{company_name, contact_name, email, title, "
                    "industry, employee_count, pain_point, score, reason}]."
                ),
            ),
            AgentConfig(
                role="researcher",
                name="Tech Stack Researcher",
                default_prompt=(
                    "You are a Tech Stack & Competitor Researcher for B2B SaaS sales. "
                    "Given a company, research: current tools they use (from job listings, "
                    "LinkedIn, BuiltWith), competitor products they might already use, "
                    "and recent news indicating budget or growth signals. "
                    "Return structured JSON research brief."
                ),
            ),
            AgentConfig(
                role="outreach",
                name="Trial Converter",
                default_prompt=(
                    "You are a Trial Conversion specialist for B2B SaaS. "
                    "Write personalised emails that: reference the prospect's specific stack "
                    "or pain point, mention a relevant customer success story, and offer "
                    "a free trial or personalised demo. Keep under 100 words. "
                    "Return JSON: {subject, body}."
                ),
            ),
            AgentConfig(
                role="delivery",
                name="Sales Brief Agent",
                default_prompt=(
                    "Compile all prospect research into a concise sales brief for an AE. "
                    "Include: Company snapshot, tech stack, pain points, "
                    "recommended demo angle, potential objections, and suggested pricing tier."
                ),
            ),
            AgentConfig(
                role="manager",
                name="Pipeline Manager",
                default_prompt=(
                    "You coordinate hunter, researcher, outreach, and delivery for SaaS GTM. "
                    "Break goals into sequenced tasks with owners. "
                    "Return JSON: {\"plan\": [{\"step\": 1, \"role\": \"hunter\", "
                    "\"task_type\": \"icp_search\", \"description\": \"...\"}]}"
                ),
            ),
        ]

    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                name="Outbound PLG Pipeline",
                dag_config={
                    "nodes": [
                        {"id": "hunt", "role": "hunter", "task_type": "icp_search"},
                        {"id": "research", "role": "researcher", "task_type": "tech_stack_research"},
                        {"id": "outreach", "role": "outreach", "task_type": "trial_invite"},
                        {"id": "deliver", "role": "delivery", "task_type": "sales_brief"},
                    ],
                    "edges": [
                        {"from": "hunt", "to": "research"},
                        {"from": "research", "to": "outreach"},
                        {"from": "outreach", "to": "deliver"},
                    ],
                },
            ),
        ]

    def get_default_skills(self) -> list[PluginSkillDoc]:
        return [
            PluginSkillDoc(
                name="ICP Qualification for B2B SaaS",
                role_tags=["hunter"],
                content_md="""# ICP Qualification for B2B SaaS

## When to use
Qualifying inbound or outbound leads against a SaaS product's Ideal Customer Profile.

## Steps
1. Confirm company size matches target segment (e.g. 50-500 employees).
2. Verify industry vertical is in scope.
3. Identify a concrete pain point the product solves (from job descriptions, news, reviews).
4. Check for budget signals: recent funding, headcount growth, competitor contract expiry.
5. Score 0.0–1.0; discard if < 0.5.

## Watch-outs
- SMBs churn faster — weight mid-market higher.
- Check G2/Capterra for negative reviews about incumbent tools (opportunity signal).
""",
            ),
            PluginSkillDoc(
                name="Competitive Intel Brief",
                role_tags=["researcher"],
                content_md="""# Competitive Intel Brief

## When to use
Mapping competitors, pricing pages, and differentiation before outreach.

## Steps
1. List top 3 alternatives the prospect likely evaluates.
2. Capture public pricing signals (seat-based, usage-based, hidden enterprise).
3. Note integration requirements (SSO, SCIM, SOC2).
4. Summarise win themes vs each competitor in one table.
""",
            ),
            PluginSkillDoc(
                name="Sales Brief Assembly",
                role_tags=["delivery"],
                content_md="""# AE-Ready Sales Brief

## Sections
- Snapshot & ICP fit
- Tech stack + migration risk
- Talk track & demo storyline
- Landmines & objection handling
- Pricing guardrails

## Rule
Every claim must trace back to a research bullet or lead field.
""",
            ),
            PluginSkillDoc(
                name="Cross-Functional Sprint Plan",
                role_tags=["manager"],
                content_md="""# PLG + Outbound Sprint

## Cadence
- Day 0–1: Hunter expands TAM list; Researcher enriches top 20.
- Day 2: Outreach runs parallel sequences; Delivery publishes daily digest.
- Day 5: Retro on reply-rate; adjust messaging via memory tags.

## Exit criteria
Minimum 3 qualified replies or explicit learnings documented for evolution.
""",
            ),
        ]

    def get_kpi_definition(self) -> KPIDefinition:
        return KPIDefinition(
            formula=(
                "base = 0.50 × success_rate + 0.30 × quality_score - 0.20 × token_norm; "
                "× 1.4 if trial_started; × 1.3 if demo_booked; × 0.6 if unsubscribed"
            )
        )

    def get_required_tools(self) -> list[str]:
        return ["resend"]
