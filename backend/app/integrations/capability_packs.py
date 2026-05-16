"""Preset capability bundles for digital employees and workflow templates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CapabilityPack:
    id: str
    display_name: str
    description: str
    capability_refs: tuple[str, ...]
    roles_hint: tuple[str, ...] = ()


CAPABILITY_PACKS: tuple[CapabilityPack, ...] = (
    CapabilityPack(
        id="gtm_outreach",
        display_name="GTM Outreach",
        description="Apollo search + Resend email for hunter/outreach roles.",
        capability_refs=("apollo_search@v1", "resend_email@v1"),
        roles_hint=("hunter", "outreach", "sdr", "bd"),
    ),
    CapabilityPack(
        id="ops_notify",
        display_name="Ops Notifications",
        description="Slack, Feishu, WeChat Work, Discord webhooks.",
        capability_refs=(
            "slack_post_message@v1",
            "feishu_lark_notify@v1",
            "wechat_work_notify@v1",
            "discord_post_message@v1",
        ),
        roles_hint=("operations", "manager", "support"),
    ),
    CapabilityPack(
        id="social_broadcast",
        display_name="Social Broadcast",
        description="X, LinkedIn, Telegram for marketing/community.",
        capability_refs=(
            "twitter_x_post@v1",
            "linkedin_share@v1",
            "telegram_send_message@v1",
        ),
        roles_hint=("marketing", "community", "pr", "founder"),
    ),
    CapabilityPack(
        id="hr_finance_notify",
        display_name="HR / Finance Alerts",
        description="Enterprise messaging for HR and finance ops.",
        capability_refs=("wechat_work_notify@v1", "feishu_lark_notify@v1", "resend_email@v1"),
        roles_hint=("hr", "finance", "operations"),
    ),
    CapabilityPack(
        id="context_sync",
        display_name="Context Sync",
        description="Gmail, Google Calendar, and GitHub auto-context (TEO-DUAL M02).",
        capability_refs=("context_sync_run@v1",),
        roles_hint=("manager", "operations", "researcher", "hunter", "outreach"),
    ),
    CapabilityPack(
        id="desktop_automation",
        display_name="Desktop Automation",
        description="Cloud sandbox computer use via Agent-S (TEO-DUAL M03).",
        capability_refs=(
            "computer_use_submit@v1",
            "computer_use_status@v1",
            "computer_use_cancel@v1",
        ),
        roles_hint=("delivery", "operations", "researcher"),
    ),
    CapabilityPack(
        id="discipline_ultrawork",
        display_name="Discipline Ultrawork",
        description=(
            "Context sync + outreach + ops notify — persistent multi-tool execution "
            "(omo-inspired harness bundle)."
        ),
        capability_refs=(
            "context_sync_run@v1",
            "apollo_search@v1",
            "resend_email@v1",
            "slack_post_message@v1",
            "research_web_search@v1",
            "research_docs_fetch@v1",
        ),
        roles_hint=("manager", "hunter", "outreach", "operations", "researcher"),
    ),
    CapabilityPack(
        id="parallel_team",
        display_name="Parallel Team",
        description="Parallel sub-agents via Celery (omo Team Mode, M07a).",
        capability_refs=(
            "research_web_search@v1",
            "research_docs_fetch@v1",
            "context_sync_run@v1",
        ),
        roles_hint=("manager", "researcher", "hunter", "outreach", "delivery"),
    ),
    CapabilityPack(
        id="research_assistant",
        display_name="Research Assistant",
        description="Web search + doc fetch for deep research roles (M07b).",
        capability_refs=("research_web_search@v1", "research_docs_fetch@v1"),
        roles_hint=("researcher", "manager", "strategy_director", "hunter", "bd"),
    ),
)


def list_capability_packs(*, role: str | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for pack in CAPABILITY_PACKS:
        if role and pack.roles_hint and role not in pack.roles_hint:
            continue
        rows.append(
            {
                "id": pack.id,
                "display_name": pack.display_name,
                "description": pack.description,
                "capability_refs": list(pack.capability_refs),
                "roles_hint": list(pack.roles_hint),
            }
        )
    return rows


def get_capability_pack(pack_id: str) -> CapabilityPack | None:
    for pack in CAPABILITY_PACKS:
        if pack.id == pack_id:
            return pack
    return None


def capability_refs_to_grant_ids(refs: tuple[str, ...] | list[str]) -> list[str]:
    """Resolve versioned refs to canonical catalog ids for tenant grants."""
    from app.integrations.catalog import CAPABILITY_INDEX
    from app.integrations.capability_version import resolve_capability_ref

    ids: list[str] = []
    for raw in refs:
        resolved = resolve_capability_ref(str(raw).strip(), index=CAPABILITY_INDEX)
        if resolved is not None:
            ids.append(resolved.canonical_id)
    return list(dict.fromkeys(ids))


def merge_grant_ids(
    current: list[str] | None,
    pack_ids: list[str],
    *,
    merge: bool,
) -> list[str]:
    if merge and current:
        return list(dict.fromkeys([*current, *pack_ids]))
    return list(dict.fromkeys(pack_ids))
