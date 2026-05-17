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
