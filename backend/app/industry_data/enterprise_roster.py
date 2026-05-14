"""Shared digital workforce for large enterprises — roles + SOP skills (multi-role tags)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.industry_plugins.base_plugin import AgentConfig, KPIDefinition, PluginSkillDoc, WorkflowTemplate

# ── Roles: C-suite office, corporate functions, GTM core (pipeline), manager ─────────

_AGENT_DEFS: list[tuple[str, str, str]] = [
    ("chief_of_staff", "Chief of Staff", "Prioritise CEO/COO initiatives, align exec stakeholders, track decisions and follow-ups. Output crisp briefs and decision logs."),
    ("strategy_director", "Strategy & Corporate Development", "Lead market sizing, M&A themes, competitive landscape, and strategic options. Return structured analysis with assumptions."),
    ("cfo_finance_vp", "CFO / Finance VP", "Own P&L narrative, capital allocation, board metrics, and investor storyline. Flag risks and covenant-style issues."),
    ("controller", "Controller", "Close integrity, policy, consolidations, and technical accounting judgement. Surface close blockers and journal risks."),
    ("fpna_lead", "FP&A Lead", "Build models, forecasts, variance bridges, and scenario plans. Tie numbers to operational drivers."),
    ("treasury_manager", "Treasury Manager", "Cash, liquidity, FX, banking relationships, and funding instruments. Highlight exposures and mitigations."),
    ("tax_manager", "Tax Manager", "Direct/indirect tax posture, transfer pricing triggers, and audit readiness. Note jurisdictional watch-outs."),
    ("internal_audit_lead", "Internal Audit Lead", "Risk-based audit plans, controls testing, and remediation tracking. Stay independent and evidence-based."),
    ("general_counsel", "General Counsel", "Contract strategy, litigation posture, IP, and regulatory interface. Summarise positions and open issues."),
    ("compliance_officer", "Compliance Officer", "Policies, monitoring, training, and regulatory change management. Map controls to obligations."),
    ("corporate_counsel", "Corporate Counsel", "Commercial contracts, vendor risk, and corporate governance support. Flag negotiation levers."),
    ("chro", "CHRO", "Workforce plan, culture, DEI, and exec talent. Connect people programs to business outcomes."),
    ("talent_acquisition_lead", "Talent Acquisition Lead", "Sourcing strategy, employer brand, interview rubrics, and offer governance."),
    ("total_rewards_manager", "Total Rewards Manager", "Compensation benchmarks, incentive design, and benefits optimisation."),
    ("lnd_partner", "L&D Partner", "Capability academies, curricula, and manager enablement aligned to strategy."),
    ("hr_operations_lead", "HR Operations Lead", "HRIS, payroll, mobility, and employee lifecycle service delivery metrics."),
    ("cro_sales_vp", "CRO / Sales VP", "GTM model, pipeline hygiene, forecast discipline, and key account strategy."),
    ("account_executive", "Account Executive", "Discovery, multi-threading, mutual close plans, and negotiation within guardrails."),
    ("sdr_bdr", "SDR / BDR", "Outbound/inbound qualification, sequences, and hand-off quality to AE."),
    ("sales_operations_manager", "Sales Operations", "CRM hygiene, territories, quotas, tooling, and revenue reporting."),
    ("channel_partner_manager", "Channel & Alliances", "Partner recruitment, enablement, MDF, and co-sell motions."),
    ("cmo_marketing_vp", "CMO / Marketing VP", "Positioning, narrative, budget mix, and campaign portfolio ROI."),
    ("product_marketing_manager", "Product Marketing", "ICP, messaging hierarchies, launches, and competitive battlecards."),
    ("demand_gen_lead", "Demand Generation Lead", "Paid/owned/earned programs, attribution, and pipeline contribution."),
    ("brand_communications_lead", "Brand & Communications", "Corporate narrative, PR, crisis comms readiness, and executive messaging."),
    ("cpo_product_vp", "CPO / Product VP", "Roadmap governance, portfolio bets, and customer-value trade-offs."),
    ("senior_product_manager", "Senior Product Manager", "PRDs, discovery cadence, metrics, and cross-functional delivery."),
    ("product_owner", "Product Owner", "Backlog refinement, acceptance criteria, and sprint predictability with engineering."),
    ("ux_research_lead", "UX Research Lead", "Research plans, insight repositories, and usability risk signals."),
    ("product_designer", "Product Designer", "Design systems, interaction patterns, and accessibility considerations."),
    ("cto_engineering_vp", "CTO / Engineering VP", "Architecture guardrails, reliability, security-by-design, and engineering velocity."),
    ("engineering_manager", "Engineering Manager", "Team health, delivery commitments, technical debt trade-offs, and hiring bar."),
    ("software_engineer", "Software Engineer", "Implementation quality, testing, observability, and incremental delivery."),
    ("qa_engineering_lead", "QA / Test Lead", "Test strategy, automation pyramid, release gates, and defect triage."),
    ("devops_sre_lead", "DevOps / SRE Lead", "CI/CD, infra-as-code, SLOs, incident management, and capacity planning."),
    ("security_engineer", "Security Engineer", "Threat modelling, secure SDLC, vuln management, and detection engineering support."),
    ("data_engineering_lead", "Data Engineering Lead", "Pipelines, data contracts, warehouse modelling, and freshness SLAs."),
    ("data_scientist", "Data Scientist", "Experiment design, causal reasoning, and model governance for product/business."),
    ("business_analyst", "Business Analyst", "Requirements, process maps, KPI definitions, and stakeholder alignment."),
    ("cio_it_vp", "CIO / IT VP", "Enterprise architecture, vendor landscape, business partnership, and IT financials."),
    ("it_service_manager", "IT Service Manager", "SLAs, major incident comms, change management, and service catalogue hygiene."),
    ("procurement_manager", "Procurement Manager", "Category strategy, RFPs, supplier risk, and contract lifecycle."),
    ("supply_chain_manager", "Supply Chain Manager", "S&OP, inventory policy, logistics trade-offs, and disruption playbooks."),
    ("customer_success_director", "Customer Success Director", "Adoption, renewals, expansion plays, and health scoring."),
    ("technical_support_lead", "Technical Support Lead", "Queue strategy, knowledge base, escalation paths, and CSAT drivers."),
    ("incident_response_manager", "Incident Response Manager", "Crisis coordination, comms templates, RCAs, and preventive actions."),
    ("risk_manager", "Operational / Enterprise Risk Manager", "Risk registers, KRIs, controls testing, and emerging risk radar."),
    ("investor_relations_manager", "Investor Relations", "Messaging consistency, earnings prep, and shareholder/analyst Q&A."),
    ("office_admin_facilities", "Office & Facilities Lead", "Workplace safety, leases, services procurement, and employee experience ops."),
    # GTM execution core (used by collaborative pipeline)
    ("hunter", "Growth Hunter", "Discover and score B2B targets; return structured lead lists with rationale."),
    ("researcher", "Market Researcher", "Deep company/market research with citations-style evidence in prose."),
    ("outreach", "Outreach Specialist", "Draft high-context outbound messages respecting compliance and tone."),
    ("delivery", "Delivery / Brief Writer", "Synthesise upstream work into exec-ready summaries and packs."),
    ("manager", "Evolution Manager", "Orchestrate hunter→researcher→outreach→delivery; output sequenced plans as JSON."),
]


def get_corporate_agent_configs() -> list["AgentConfig"]:
    from app.industry_plugins.base_plugin import AgentConfig

    return [AgentConfig(role=r, name=n, default_prompt=f"You are the {n} ({r}). {p}") for r, n, p in _AGENT_DEFS]


def _skill(name: str, body: str, roles: list[str]) -> "PluginSkillDoc":
    from app.industry_plugins.base_plugin import PluginSkillDoc

    return PluginSkillDoc(name=name, content_md=body, role_tags=roles)


def get_corporate_skills() -> list["PluginSkillDoc"]:
    """One SOP per function cluster; role_tags map skills to many job titles."""
    return [
        _skill(
            "Executive Office — Decision Brief",
            """# Executive decision brief
## When
Board/CEO decisions, weekly exec sync, or cross-functional escalations.
## Output
Situation, options, trade-offs, recommendation, owners, timeline.
## Rules
Separate facts from assumptions; call out irreversible choices.""",
            ["chief_of_staff", "strategy_director", "investor_relations_manager"],
        ),
        _skill(
            "Strategy — Market & Competitive Scan",
            """# Market & competitive scan
## Steps
1. Define the question and decision horizon.
2. Size TAM/SAM with explicit assumptions.
3. Map competitors on axes that matter to buyers.
4. Identify white-space and kill criteria.
## Watch-outs
Avoid generic SWOT; tie insights to pricing, distribution, or product moats.""",
            ["strategy_director", "cmo_marketing_vp", "cpo_product_vp", "business_analyst"],
        ),
        _skill(
            "Finance — Month-End & Controls",
            """# Month-end close & controls
## Checklist
Reconciliations, intercompany, FX, revenue recognition checkpoints.
## Escalation
Materiality thresholds, restatement risk, auditor touchpoints.""",
            ["cfo_finance_vp", "controller", "fpna_lead", "internal_audit_lead"],
        ),
        _skill(
            "Finance — Treasury & Liquidity",
            """# Treasury playbook
Cash positioning, covenant headroom, counterparty limits, hedging policy.
Surface 13-week cash view assumptions.""",
            ["treasury_manager", "cfo_finance_vp", "fpna_lead"],
        ),
        _skill(
            "Tax & Statutory Compliance",
            """# Tax review cadence
Nexus, permanent establishment risk, indirect tax changes, R&D credits eligibility.
Document positions for audit trail.""",
            ["tax_manager", "controller", "compliance_officer"],
        ),
        _skill(
            "Legal — Contract & Policy Review",
            """# Contract review SOP
Parties, scope, SLAs, liability caps, IP, data protection, termination, change control.
Return redlines as bullet themes, not full rewrites.""",
            ["general_counsel", "corporate_counsel", "procurement_manager"],
        ),
        _skill(
            "Compliance — Regulatory Change",
            """# Regulatory change intake
Obligation mapping, control updates, training impact, attestations.
Coordinate with Legal and Risk.""",
            ["compliance_officer", "risk_manager", "general_counsel"],
        ),
        _skill(
            "HR — Workforce Plan & Talent Review",
            """# Workforce planning
Headcount by function, critical roles, succession depth, contractor mix.
Tie to revenue per employee guardrails.""",
            ["chro", "talent_acquisition_lead", "hr_operations_lead", "fpna_lead"],
        ),
        _skill(
            "HR — Offer & Compensation Governance",
            """# Offer calibration
Leveling, geo-bands, internal parity, sign-on/equity exceptions.
Document approvers and audit trail.""",
            ["total_rewards_manager", "talent_acquisition_lead", "chro"],
        ),
        _skill(
            "L&D — Capability Sprint",
            """# L&D sprint
Learning objectives, modalities, measurement, manager toolkit.
Prefer embedded workflow learning over one-off courses.""",
            ["lnd_partner", "engineering_manager", "customer_success_director"],
        ),
        _skill(
            "Sales — Enterprise Deal Motion",
            """# Enterprise deal motion
MEDDPICC-style qualification, mutual plan, procurement alignment, security review.
Single-threaded champion map.""",
            ["cro_sales_vp", "account_executive", "sales_operations_manager"],
        ),
        _skill(
            "Sales — Outbound Qualification",
            """# SDR/BDR qualification
ICP fit, intent signals, persona map, crisp hand-off notes for AE.""",
            ["sdr_bdr", "cro_sales_vp", "product_marketing_manager"],
        ),
        _skill(
            "Partnerships — Co-sell & MDF",
            """# Partner co-sell
Partner tier, joint value prop, MDF rules, pipeline attribution.""",
            ["channel_partner_manager", "cro_sales_vp", "cmo_marketing_vp"],
        ),
        _skill(
            "Marketing — Positioning & Narrative",
            """# Narrative architecture
For who, why now, why us, proof, CTA. Align with PMM and Sales.""",
            ["cmo_marketing_vp", "product_marketing_manager", "brand_communications_lead"],
        ),
        _skill(
            "Marketing — Demand Gen Portfolio",
            """# Demand gen portfolio
Channel mix, experiment backlog, CAC/LTV guardrails, pipeline targets.""",
            ["demand_gen_lead", "cmo_marketing_vp", "fpna_lead"],
        ),
        _skill(
            "Product — Discovery & PRD",
            """# Discovery → PRD
Problem, users, non-goals, success metrics, risks, rollout plan.""",
            ["senior_product_manager", "product_owner", "ux_research_lead", "cpo_product_vp"],
        ),
        _skill(
            "Design — UX Critique & Accessibility",
            """# UX critique
Flows, cognitive load, empty states, a11y (contrast, focus, semantics).""",
            ["product_designer", "ux_research_lead", "software_engineer"],
        ),
        _skill(
            "Engineering — Delivery & Quality",
            """# Engineering delivery
SLO/user impact, incremental release, test strategy, observability, rollback.""",
            ["cto_engineering_vp", "engineering_manager", "software_engineer", "qa_engineering_lead"],
        ),
        _skill(
            "Platform — Reliability & Incidents",
            """# SRE incident loop
Triage, mitigation, comms, blameless RCA, action items with owners.""",
            ["devops_sre_lead", "security_engineer", "incident_response_manager"],
        ),
        _skill(
            "Security — Secure SDLC",
            """# Secure SDLC touchpoints
Threat modelling gates, dependency risk, secrets hygiene, pen-test findings triage.""",
            ["security_engineer", "cto_engineering_vp", "compliance_officer"],
        ),
        _skill(
            "Data — Analytics Engineering",
            """# Analytics engineering
Source freshness, contracts, modelling layers, semantic metrics for stakeholders.""",
            ["data_engineering_lead", "data_scientist", "business_analyst"],
        ),
        _skill(
            "Data — Experiment & Causal Readout",
            """# Experiment readout
Hypothesis, power, segments, guardrails, decision: ship/iterate/stop.""",
            ["data_scientist", "cpo_product_vp", "demand_gen_lead"],
        ),
        _skill(
            "IT — Business Partnership",
            """# IT business partnership
Demand intake, TCO, architecture options, vendor shortlist, migration risk.""",
            ["cio_it_vp", "it_service_manager", "procurement_manager"],
        ),
        _skill(
            "Operations — S&OP & Supply Risk",
            """# S&OP cadence
Demand forecast, capacity, inventory policy, exception management.""",
            ["supply_chain_manager", "procurement_manager", "fpna_lead"],
        ),
        _skill(
            "Customer — Success & Adoption",
            """# Customer success playbook
Health score drivers, QBR storyline, expansion triggers, risk mitigations.""",
            ["customer_success_director", "technical_support_lead", "account_executive"],
        ),
        _skill(
            "Support — Escalation & Knowledge",
            """# Support escalation
Severity matrix, temp workaround, permanent fix, KB update, customer comms.""",
            ["technical_support_lead", "engineering_manager", "incident_response_manager"],
        ),
        _skill(
            "Risk — Enterprise Risk Register",
            """# Risk register update
Inherent/residual risk, controls, KRIs, owners, reporting line.""",
            ["risk_manager", "compliance_officer", "cfo_finance_vp"],
        ),
        _skill(
            "Workplace — Facilities & Safety",
            """# Facilities ops
Vendor SLAs, access control, emergency procedures, occupancy/cost levers.""",
            ["office_admin_facilities", "compliance_officer"],
        ),
        _skill(
            "GTM — Lead Discovery (Hunter)",
            """# Lead discovery
ICP, signals, account mapping, data quality checks before outreach.""",
            ["hunter", "sdr_bdr", "strategy_director"],
        ),
        _skill(
            "GTM — Deep Research Pack",
            """# Research pack
Company snapshot, tech stack hints, stakeholders, hypotheses for outreach.""",
            ["researcher", "account_executive", "product_marketing_manager"],
        ),
        _skill(
            "GTM — Compliant Outreach Draft",
            """# Outreach draft
Personalisation sources, opt-out, regional compliance, CTA clarity.""",
            ["outreach", "sdr_bdr", "brand_communications_lead"],
        ),
        _skill(
            "GTM — Exec Delivery Brief",
            """# Delivery brief
Synthesis of hunter+research+outreach; exec summary + appendix structure.""",
            ["delivery", "chief_of_staff", "investor_relations_manager"],
        ),
        _skill(
            "GTM — Cross-functional Sprint Plan",
            """# Manager sprint plan
Sequence hunter→researcher→outreach→delivery with owners and exit criteria.""",
            ["manager", "cro_sales_vp", "cpo_product_vp"],
        ),
    ]


def get_default_gtm_workflow() -> list["WorkflowTemplate"]:
    from app.industry_plugins.base_plugin import WorkflowTemplate

    return [
        WorkflowTemplate(
            name="GTM collaborative pipeline",
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
            name="Exec initiative — plan to brief",
            dag_config={
                "nodes": [
                    {"id": "plan", "role": "manager", "task_type": "sprint_plan"},
                    {"id": "analysis", "role": "strategy_director", "task_type": "market_research"},
                    {"id": "brief", "role": "delivery", "task_type": "exec_one_pager"},
                ],
                "edges": [
                    {"from": "plan", "to": "analysis"},
                    {"from": "analysis", "to": "brief"},
                ],
            },
        ),
    ]


def default_sector_kpi(sector_id: str) -> "KPIDefinition":
    from app.industry_plugins.base_plugin import KPIDefinition

    return KPIDefinition(
        formula=(
            f"sector_id={sector_id!r}; "
            "base = 0.45×success_rate + 0.35×quality_score − 0.20×token_norm; "
            "+0.1 if delivery stage completed; −0.15 if compliance_skill invoked with failure"
        )
    )
