"""Discipline agent harness — orchestration patterns for Titan B2B agents.

Inspired by oh-my-openagent (omo) concepts: intent clarity, category routing,
and persistent tool loops. We implement these inside Titan's tenant-scoped stack,
not as an OpenCode plugin.

Reference: https://github.com/code-yeongyu/oh-my-openagent
"""
from __future__ import annotations

import re
from typing import Any

HARNESS_MODES = frozenset({"standard", "ultrawork", "plan_first"})

ROLE_CATEGORY: dict[str, str] = {
    "manager": "orchestrate",
    "strategy_director": "ultrabrain",
    "researcher": "deep",
    "hunter": "deep",
    "outreach": "quick",
    "delivery": "deep",
    "operations": "quick",
    "marketing": "visual",
    "community": "quick",
    "support": "quick",
    "hr": "quick",
    "finance": "quick",
    "founder": "orchestrate",
    "pr": "visual",
    "sdr": "quick",
    "bd": "deep",
    "customer_success": "quick",
}

_CATEGORY_DEFAULTS: dict[str, str] = {
    "orchestrate": "Plan, delegate, and drive tasks to completion. Prefer parallel tool use when safe.",
    "deep": "Explore context thoroughly before acting. Use tools to verify facts.",
    "quick": "Minimize scope; prefer the smallest change that satisfies the goal.",
    "visual": "Prioritize clarity of user-facing copy and structure.",
    "ultrabrain": "Resolve ambiguity with explicit trade-offs before execution.",
}


def role_category(role: str) -> str:
    key = (role or "").strip().lower()
    return ROLE_CATEGORY.get(key, "deep")


def resolve_harness_mode(task_input: dict[str, Any] | None, tenant_config: dict[str, Any] | None) -> str:
    inp = task_input if isinstance(task_input, dict) else {}
    cfg = tenant_config if isinstance(tenant_config, dict) else {}
    harness_cfg = cfg.get("harness") if isinstance(cfg.get("harness"), dict) else {}

    raw = inp.get("harness_mode")
    if isinstance(raw, str) and raw.strip().lower() in HARNESS_MODES:
        return raw.strip().lower()
    if inp.get("ultrawork") is True:
        return "ultrawork"
    default = harness_cfg.get("default_mode")
    if isinstance(default, str) and default.strip().lower() in HARNESS_MODES:
        return default.strip().lower()
    return "standard"


def max_tool_rounds_for_mode(mode: str) -> int:
    return {"standard": 3, "ultrawork": 8, "plan_first": 5}.get(mode, 3)


def intent_gate_heuristic(goal: str) -> dict[str, str]:
    """Lightweight intent gate (no extra LLM) — clarifies goal before routing."""
    text = (goal or "").strip()
    lowered = text.lower()
    if not text:
        return {"true_intent": "", "success_criteria": "Complete the stated business goal."}

    # Strip common filler prefixes (omo IntentGate-style disambiguation, rule-based).
    for prefix in (
        r"^(please|pls|can you|could you|i need you to|help me)\s+",
        r"^(帮我|请|麻烦|能否|能不能)",
    ):
        text = re.sub(prefix, "", text, flags=re.I).strip()

    success = "Deliver a concrete, verifiable outcome aligned with the user's goal."
    if any(w in lowered for w in ("research", "analyze", "analysis", "调研", "分析")):
        success = "Produce structured findings with sources or tool-backed evidence."
    elif any(w in lowered for w in ("email", "outreach", "send", "notify", "邮件", "通知")):
        success = "Send or draft the message and confirm delivery or draft artifacts."
    elif any(w in lowered for w in ("fix", "bug", "error", "修复", "报错")):
        success = "Identify root cause and apply or recommend a verified fix."

    return {"true_intent": text[:500], "success_criteria": success}


def discipline_system_addon(
    *,
    mode: str,
    category: str,
    intent: dict[str, str] | None = None,
) -> str:
    cat_hint = _CATEGORY_DEFAULTS.get(category, _CATEGORY_DEFAULTS["deep"])
    lines = [
        "[Discipline harness]",
        f"Work category: {category}. {cat_hint}",
    ]
    if intent and intent.get("true_intent"):
        lines.append(f"True intent: {intent['true_intent']}")
    if intent and intent.get("success_criteria"):
        lines.append(f"Done when: {intent['success_criteria']}")
    if mode == "ultrawork":
        lines.append(
            "Ultrawork: keep calling tools until the goal is fully done or blocked; "
            "do not stop at partial progress. Summarize blockers explicitly."
        )
    elif mode == "plan_first":
        lines.append(
            "Plan-first: outline steps in the JSON summary before heavy tool use; "
            "then execute and update next_actions."
        )
    if category == "deep" or mode == "ultrawork":
        from app.agents.hashline_edit import format_hashline_prompt_snippet

        lines.append(format_hashline_prompt_snippet())
    return "\n".join(lines)


def project_context_block(tenant_config: dict[str, Any] | None) -> str:
    """Inject tenant-level AGENTS.md-style context (omo /init-deep pattern)."""
    if not isinstance(tenant_config, dict):
        return ""
    harness = tenant_config.get("harness")
    if not isinstance(harness, dict):
        return ""
    raw = harness.get("project_context") or harness.get("agents_md")
    if isinstance(raw, str) and raw.strip():
        return "\n\n[Project context]\n" + raw.strip()[:12000]
    return ""
