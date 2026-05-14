"""Payment & Fintech industry plugin — B2B payments / acquiring / fintech go-to-market."""
from __future__ import annotations

from app.industry_data.enterprise_roster import (
    merge_corporate_agents_with_plugin_gtm,
    merge_corporate_and_plugin_skills,
)
from app.industry_plugins.base_plugin import (
    AgentConfig,
    IndustryPlugin,
    KPIDefinition,
    PluginSkillDoc,
    WorkflowTemplate,
)


def _payment_fintech_gtm_overrides() -> list[AgentConfig]:
    return [
        AgentConfig(
            role="hunter",
            name="Growth Hunter",
            default_prompt=(
                "You are a Growth Hunter for a B2B payment / fintech company. "
                "Your mission: identify merchants, platforms, or fintechs that need "
                "payment processing, acquiring, or embedded finance. "
                "Target: Head of Payments, CPO, CFO, or Founder at companies with "
                "10-500 employees in MENA, SEA, or LatAm markets. "
                "Return leads as JSON: [{company_name, contact_name, email, "
                "title, industry, country, company_size, score, reason}]."
            ),
        ),
        AgentConfig(
            role="researcher",
            name="License Researcher",
            default_prompt=(
                "You are a License & Compliance Researcher for fintech deals. "
                "Given a company name and country, research: "
                "1) What payment/financial licenses they hold (if any). "
                "2) What licenses they need to operate in their target market. "
                "3) Key regulatory contacts or consultants. "
                "4) Estimated license acquisition timeline and cost. "
                "Return a structured JSON research brief."
            ),
        ),
        AgentConfig(
            role="outreach",
            name="Outreach Agent",
            default_prompt=(
                "You are a B2B outreach specialist for a payment infrastructure company. "
                "Write concise, personalised cold emails (≤120 words). "
                "Focus on: reducing payment failure rates, faster settlement, "
                "local payment method support, or regulatory compliance. "
                "Never use generic phrases like 'I hope this email finds you well'. "
                "Return JSON: {subject, body}."
            ),
        ),
        AgentConfig(
            role="delivery",
            name="Deal Summary Agent",
            default_prompt=(
                "You are a Deal Summary specialist. Compile all research and "
                "outreach data into a professional deal brief in Markdown. "
                "Include: Executive Summary, Company Profile, Opportunity Size, "
                "Recommended Approach, Next Steps, Risk Factors."
            ),
        ),
        AgentConfig(
            role="manager",
            name="Evolution Manager",
            default_prompt=(
                "You are an Evolution Manager coordinating hunter, researcher, outreach, "
                "and delivery work. Break goals into ordered steps with clear owners. "
                "Return JSON: {\"plan\": [{\"step\": 1, \"role\": \"hunter\", "
                "\"task_type\": \"lead_search\", \"description\": \"...\"}]}"
            ),
        ),
    ]


class PaymentFintechPlugin(IndustryPlugin):

    @property
    def plugin_id(self) -> str:
        return "payment_fintech"

    @property
    def display_name(self) -> str:
        return "Payment & Fintech"

    # ── Agent configurations ───────────────────────────────────────────────

    def get_agent_configs(self) -> list[AgentConfig]:
        return merge_corporate_agents_with_plugin_gtm(_payment_fintech_gtm_overrides())

    # ── Workflow templates ─────────────────────────────────────────────────

    def get_workflow_templates(self) -> list[WorkflowTemplate]:
        return [
            WorkflowTemplate(
                name="Full GTM Pipeline",
                dag_config={
                    "nodes": [
                        {"id": "hunt", "role": "hunter", "task_type": "lead_search"},
                        {"id": "research", "role": "researcher", "task_type": "company_research"},
                        {"id": "outreach", "role": "outreach", "task_type": "email_write"},
                        {"id": "deliver", "role": "delivery", "task_type": "deal_summary"},
                    ],
                    "edges": [
                        {"from": "hunt", "to": "research"},
                        {"from": "research", "to": "outreach"},
                        {"from": "outreach", "to": "deliver"},
                    ],
                },
            ),
            WorkflowTemplate(
                name="Quick Outreach",
                dag_config={
                    "nodes": [
                        {"id": "hunt", "role": "hunter", "task_type": "lead_search"},
                        {"id": "outreach", "role": "outreach", "task_type": "email_write"},
                    ],
                    "edges": [{"from": "hunt", "to": "outreach"}],
                },
            ),
        ]

    # ── Default skill docs ─────────────────────────────────────────────────

    def get_default_skills(self) -> list[PluginSkillDoc]:
        return merge_corporate_and_plugin_skills([
            PluginSkillDoc(
                name="MENA Payment Lead Qualification",
                role_tags=["hunter"],
                content_md="""# MENA Payment Lead Qualification

## When to use
Qualifying B2B leads for payment infrastructure solutions in MENA markets
(UAE, Saudi Arabia, Egypt, Jordan, Kuwait).

## Prerequisites
- Company name and basic profile
- Target country or region

## Steps
1. Verify company operates in or targets MENA markets.
2. Check if company processes >$500K/year in transactions (target segment).
3. Confirm contact has payment/financial authority (Head of Payments, CFO, CPO).
4. Score: +0.3 if e-commerce, +0.2 if marketplace, +0.2 if cross-border.
5. Flag if company already has a strong incumbent processor.

## Watch-outs
- Avoid leads in heavily sanctioned markets.
- Government entities have long procurement cycles — deprioritise.
- Verify email domain matches company website.

## Example output
```json
{"score": 0.82, "reason": "UAE-based marketplace, cross-border payments, no incumbent noted"}
```""",
            ),
            PluginSkillDoc(
                name="Cold Email — Payment Infrastructure",
                role_tags=["outreach"],
                content_md="""# Cold Email — Payment Infrastructure

## When to use
Writing first-touch cold emails to payment/fintech decision-makers.

## Prerequisites
- Contact name and title
- Company name and industry
- One specific pain point or opportunity

## Steps
1. Open with a specific observation about their business (not generic praise).
2. Name one concrete problem: high decline rates / slow settlement / missing local methods.
3. State your unique value in one sentence.
4. Clear CTA: 15-minute call, demo link, or case study.
5. Keep total length ≤ 120 words.

## Watch-outs
- Never start with "I hope this email finds you well".
- Avoid technical jargon unless contact is clearly technical.
- One email = one value proposition only.

## Example subject lines
- "Reducing {{company}}'s card decline rate in KSA"
- "Local payment methods for {{company}}'s MENA expansion"
""",
            ),
            PluginSkillDoc(
                name="Fintech License Research Framework",
                role_tags=["researcher"],
                content_md="""# Fintech License Research Framework

## When to use
Researching payment/EMI/acquiring licenses for a target company or market.

## Prerequisites
- Target company name
- Operating country / target market

## Steps
1. Identify license category needed: PSP, EMI, PI, Acquiring, MSB.
2. Check central bank / financial regulator website for requirements.
3. Note minimum capital requirements and timeline (typically 6–18 months).
4. Find 2-3 local consultants or law firms specialising in fintech licensing.
5. Summarise as: Current Status / Gap / Estimated Cost & Timeline.

## Watch-outs
- Regulations change frequently — note the date of research.
- Sandbox/regulatory sandbox programmes can accelerate timelines.
- Passporting rules differ significantly inside vs outside EU.
""",
            ),
            PluginSkillDoc(
                name="Partner Ecosystem Mapping",
                role_tags=["hunter"],
                content_md="""# Partner & Channel Lead Mapping

## When to use
Finding payment aggregators, ISVs, and referral partners instead of end merchants.

## Steps
1. Tag targets: PayFac, marketplace enabler, vertical SaaS with payments.
2. Score by integration docs quality, API uptime mentions, and case studies.
3. Capture both BD lead and solution-engineering contact where possible.
4. Log competing integrations (Stripe, Adyen, local PSPs).

## Output
JSON list with partner_type, company_name, integration_readiness, score, reason.
""",
            ),
            PluginSkillDoc(
                name="Deal Desk One-Pager",
                role_tags=["delivery"],
                content_md="""# Exec One-Pager Checklist

## Sections (≤1 page)
- Thesis: why we win now.
- Company snapshot & revenue motion.
- Regulatory / settlement risk bullets.
- Mutual action plan with dates.
- Required internal approvals (Legal, Risk, Treasury).

## Tone
Crisp bullets; avoid marketing adjectives without proof points.
""",
            ),
            PluginSkillDoc(
                name="Squad Orchestration Playbook",
                role_tags=["manager"],
                content_md="""# Multi-Agent Squads

## Pattern
1. Hunter validates ICP + urgency.
2. Researcher validates factual + regulatory assumptions.
3. Outreach proposes concrete next step tied to research insight.
4. Delivery packages artifacts for AE / exec review.

## Rules of engagement
- Each step consumes prior JSON outputs (no duplicated web search).
- If Hunter finds <3 qualified leads, pause pipeline and return gaps.
- Escalate to human when compliance_flag appears in any stage.
""",
            ),
        ])

    # ── KPI definition ─────────────────────────────────────────────────────

    def get_kpi_definition(self) -> KPIDefinition:
        return KPIDefinition(
            formula=(
                "base = 0.50 × success_rate + 0.30 × quality_score - 0.20 × token_norm; "
                "× 1.3 if task leads to meeting_booked; "
                "× 0.5 if email marked as spam"
            )
        )

    def get_required_tools(self) -> list[str]:
        return ["apollo", "resend"]
