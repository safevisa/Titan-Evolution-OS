"""Curated external capability radar for Titan's daily evolution loop."""
from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class CapabilityRadarItem:
    """A market-discovered project or skill worth tracking for Titan."""

    id: str
    name: str
    url: str
    category: str
    license: str
    stars: str
    maturity: str
    titan_fit_score: float
    recommended_action: str
    integration_path: str
    risk_note: str
    source_note: str

    def to_dict(self) -> dict:
        return asdict(self)


RADAR_ITEMS: tuple[CapabilityRadarItem, ...] = (
    CapabilityRadarItem(
        id="github_mcp_server",
        name="GitHub MCP Server",
        url="https://github.com/github/github-mcp-server",
        category="mcp/devtools",
        license="MIT",
        stars="29.9k",
        maturity="official, high adoption",
        titan_fit_score=0.96,
        recommended_action="promote_to_integration_candidate",
        integration_path=(
            "Map to Context Sync + engineering agent tool pack: repo search, issues, "
            "PR triage, workflow status, and release intelligence."
        ),
        risk_note="Requires strict PAT/OAuth scope boundaries and audit logs before write actions.",
        source_note="Official GitHub MCP for repository, issue, PR, workflow, and code analysis tasks.",
    ),
    CapabilityRadarItem(
        id="context7",
        name="Context7",
        url="https://github.com/upstash/context7",
        category="mcp/docs",
        license="MIT",
        stars="55.4k",
        maturity="very high adoption",
        titan_fit_score=0.93,
        recommended_action="add_as_coding_research_skill",
        integration_path=(
            "Use as a documentation freshness layer for engineering and delivery agents; "
            "prefer MCP/CLI sidecar first, then evaluate native capability wrapper."
        ),
        risk_note="External docs retrieval should be cached and source-attributed to avoid stale or noisy context.",
        source_note="Fetches up-to-date, version-specific documentation and examples into agent context.",
    ),
    CapabilityRadarItem(
        id="conductor_oss",
        name="Conductor OSS",
        url="https://github.com/conductor-oss/conductor",
        category="workflow/orchestration",
        license="Apache-2.0",
        stars="31.8k",
        maturity="production-proven",
        titan_fit_score=0.9,
        recommended_action="study_for_durable_workflow_design",
        integration_path=(
            "Use as a reference for durable DAG replay, retries, timeouts, human approval, "
            "and observable workflow definitions around Titan goal pipelines."
        ),
        risk_note="Large Java/TS stack; do not embed directly until Titan's Celery pipeline gaps are measured.",
        source_note="Durable workflow engine with AI orchestration, MCP tool calling, and RAG support.",
    ),
    CapabilityRadarItem(
        id="toolhive",
        name="ToolHive",
        url="https://github.com/stacklok/toolhive",
        category="mcp/security-runtime",
        license="Apache-2.0",
        stars="1.8k",
        maturity="active security-focused runtime",
        titan_fit_score=0.88,
        recommended_action="evaluate_as_mcp_sandbox_runtime",
        integration_path=(
            "Borrow the governance model for Titan MCP registry: curated servers, one-click install, "
            "policy presets, container isolation, OTel, and audit logs."
        ),
        risk_note="Runtime adoption is still emerging; validate container isolation and multi-tenant boundaries.",
        source_note="Runs and manages MCP servers with registry, gateway, runtime, policy, and observability.",
    ),
    CapabilityRadarItem(
        id="apify_agent_skills",
        name="Apify Agent Skills",
        url="https://github.com/apify/agent-skills",
        category="skills/web-data",
        license="Apache-2.0",
        stars="2k",
        maturity="vendor-maintained skill pack",
        titan_fit_score=0.86,
        recommended_action="convert_to_industry_skill_templates",
        integration_path=(
            "Translate lead generation, competitor monitoring, maps/reviews, social scraping, "
            "and Actor packaging patterns into Titan SkillDocs and capability stubs."
        ),
        risk_note="Some Actors are paid or third-party; expose pricing and data compliance warnings in UI.",
        source_note="Production-grade scraping and automation skills for coding agents with MCP compatibility.",
    ),
    CapabilityRadarItem(
        id="ibm_mcp_context_forge",
        name="IBM MCP Context Forge",
        url="https://github.com/IBM/mcp-context-forge",
        category="mcp/gateway-registry",
        license="Apache-2.0 plus unknown license-policy file",
        stars="3.7k",
        maturity="enterprise-oriented gateway",
        titan_fit_score=0.82,
        recommended_action="study_not_embed",
        integration_path=(
            "Use as an architecture reference for MCP/A2A/REST federation, centralized discovery, "
            "guardrails, auth, plugins, and production test discipline."
        ),
        risk_note="GitHub reports an unknown license file; legal review required before copying any code.",
        source_note="Gateway, registry, and proxy in front of MCP, A2A, REST, and gRPC APIs.",
    ),
    # ── 2026-05-17 daily scan additions ────────────────────────────────────
    CapabilityRadarItem(
        id="browser_use",
        name="Browser Use",
        url="https://github.com/browser-use/browser-use",
        category="browser-automation",
        license="MIT",
        stars="90k",
        maturity="production-proven (v0.12), WebVoyager 89.1%",
        titan_fit_score=0.94,
        recommended_action="evaluate_as_computer_use_backend",
        integration_path=(
            "Add as optional second backend in computer-use-runner alongside Agent-S. "
            "CDP-based (no Playwright), 2x faster, 50% fewer tokens. "
            "Wire via capability param engine=browseruse."
        ),
        risk_note="Requires Chrome/Chromium in sandbox; evaluate interoperability with existing Agent-S/UI-TARS pipeline.",
        source_note="Highest-starred browser automation agent; CDP-native, self-healing, cloud browser service for CAPTCHA.",
    ),
    CapabilityRadarItem(
        id="openviking",
        name="OpenViking",
        url="https://github.com/volcengine/OpenViking",
        category="memory/context",
        license="Apache-2.0",
        stars="21.7k",
        maturity="fast-growing (228 stars/day), v0.2.x series",
        titan_fit_score=0.91,
        recommended_action="study_for_memory_tree_architecture",
        integration_path=(
            "Adopt AGFS filesystem paradigm (L0 working / L1 project / L2 long-term) "
            "for Titan Memory Tree tiered loading design. "
            "83% token savings via hierarchical context injection. "
            "Visual retrieval traces align with Titan audit requirements."
        ),
        risk_note="C++/Go dependencies for AGFS; prefer pattern adoption over runtime embedding for now.",
        source_note="ByteDance/Volcengine context database; filesystem paradigm replaces flat RAG; self-evolving agents.",
    ),
    CapabilityRadarItem(
        id="openclaw",
        name="OpenClaw",
        url="https://github.com/serif-ai/openclaw",
        category="industry/sales",
        license="to-be-confirmed",
        stars="150k+",
        maturity="production-deployed sales automation",
        titan_fit_score=0.89,
        recommended_action="convert_to_sales_plugin_template",
        integration_path=(
            "Extract 10 sales workflow patterns (lead research, pipeline reporting, "
            "competitive intelligence, meeting prep) as Titan industry plugin templates. "
            "Do NOT copy code; abstract patterns into workflow.yaml + agent_roles.yaml + SkillDocs."
        ),
        risk_note="License unconfirmed — do not copy any code until license is verified. GPL would restrict to sidecar-only reference.",
        source_note="AI sales operations agent; model-agnostic, self-hosted, cron-scheduled; 10 major sales workflows.",
    ),
    CapabilityRadarItem(
        id="statewave",
        name="Statewave",
        url="https://github.com/smaramwbc/statewave",
        category="memory/runtime",
        license="to-be-confirmed",
        stars="new (v0.7.1)",
        maturity="early-stage, actively developed",
        titan_fit_score=0.86,
        recommended_action="study_episodes_and_scoring",
        integration_path=(
            "Reference durable episode model, ranked retrieval (semantic + recency + relevance + temporal), "
            "token budget management, and customer health scoring (0-100) for Titan Memory Tree and Delivery agent."
        ),
        risk_note="Very new project; community validation thin. Architecture patterns are the primary value today.",
        source_note="Postgres+pgvector memory runtime; durable episodes, compiled memories, support-agent focused.",
    ),
    CapabilityRadarItem(
        id="ui_tars_desktop",
        name="UI-TARS Desktop",
        url="https://github.com/bytedance/UI-TARS-desktop",
        category="computer-use/grounding",
        license="Apache-2.0",
        stars="27k",
        maturity="production-proven (ByteDance internal)",
        titan_fit_score=0.92,
        recommended_action="integrate_as_grounding_model",
        integration_path=(
            "Already referenced in Titan product plan as grounding model candidate. "
            "Pure vision-driven (no DOM/API dependency), cross-platform. "
            "Evaluate as replacement or alternative to current UI-TARS-1.5-7B endpoint."
        ),
        risk_note="Vision model inference cost; GPU requirement for local hosting. HF endpoint recommended for MVP.",
        source_note="ByteDance pure-vision GUI agent; powers Doubao mobile; desktop + CLI + MCP modes; offline-capable.",
    ),
    CapabilityRadarItem(
        id="deerflow",
        name="DeerFlow 2.0",
        url="https://github.com/bytedance/deer-flow",
        category="agent-framework",
        license="Apache-2.0",
        stars="46k+",
        maturity="rapidly growing, LangGraph-based",
        titan_fit_score=0.87,
        recommended_action="study_sandbox_orchestration",
        integration_path=(
            "Reference sandboxed execution runtime pattern: Docker per task, "
            "sub-agent orchestration, long-term memory, skill system, MCP server support. "
            "Aligns with Titan Computer Use Runner + Celery task model."
        ),
        risk_note="Heavy LangChain dependency; ByteDance maintenance continuity uncertain. Use as architecture reference only.",
        source_note="ByteDance super-agent runtime; #1 GitHub Trending on release; Telegram/Slack/Lark integrations.",
    ),
    CapabilityRadarItem(
        id="tooltrim",
        name="Tooltrim",
        url="https://github.com/tooltrim/tooltrim",
        category="mcp/optimization",
        license="to-be-confirmed",
        stars="new",
        maturity="early-stage MCP proxy",
        titan_fit_score=0.84,
        recommended_action="evaluate_for_mcp_layer",
        integration_path=(
            "MCP proxy that filters and compresses tool lists across servers, reducing context bloat by 70-93% "
            "with ~3.7ms overhead. Directly applicable to Titan's MCP gateway layer for multi-MCP scenarios."
        ),
        risk_note="Early project; evaluate stability and license before any integration.",
        source_note="Lightweight MCP proxy for tool list optimization; context-window-aware filtering and tracing.",
    ),
    CapabilityRadarItem(
        id="nocobase",
        name="NocoBase",
        url="https://github.com/nocobase/nocobase",
        category="platform/ai-employees",
        license="Apache-2.0",
        stars="21.7k",
        maturity="production-deployed, 100+ contributors",
        titan_fit_score=0.83,
        recommended_action="study_ai_employee_ux",
        integration_path=(
            "Reference AI digital employee embedding pattern: Scout (sales intel), Viz (insights), "
            "Ellis (email), Dex (data), Lexi (i18n). Apply to Titan's agent role design and UX onboarding."
        ),
        risk_note="No-code platform focus differs from Titan's developer-OS positioning; patterns transfer, code does not.",
        source_note="Apache-2.0 no-code platform with AI employees deeply embedded in business processes; CRM 2.0.",
    ),
)


def list_radar_items(category: str | None = None) -> list[dict]:
    """Return radar items sorted by Titan fit score."""
    items = RADAR_ITEMS
    if category:
        normalized = category.lower()
        items = tuple(item for item in items if normalized in item.category.lower())
    return [item.to_dict() for item in sorted(items, key=lambda item: item.titan_fit_score, reverse=True)]


def radar_summary(category: str | None = None) -> dict:
    items = list_radar_items(category=category)
    return {
        "version": "2026-05-17",
        "category": category or "all",
        "item_count": len(items),
        "top_recommendations": items[:3],
        "integration_principles": [
            "Prefer sidecar or gateway integration before embedding third-party runtimes.",
            "Require license, security, tenant isolation, credential scope, and audit review.",
            "Convert proven patterns into Titan SkillDocs, capability stubs, or workflow templates first.",
            "Only promote to live capability after tests, quotas, observability, and rollback paths exist.",
        ],
    }
