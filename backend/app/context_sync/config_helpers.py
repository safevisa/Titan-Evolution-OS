"""Tenant config helpers for Context Sync."""
from __future__ import annotations

from typing import Any


def context_sync_block(tenant_config: dict[str, Any] | None) -> dict[str, Any]:
    if not tenant_config:
        return {}
    raw = tenant_config.get("context_sync")
    return raw if isinstance(raw, dict) else {}


def context_sync_enabled(tenant_config: dict[str, Any] | None) -> bool:
    return bool(context_sync_block(tenant_config).get("enabled"))


def source_enabled(tenant_config: dict[str, Any] | None, source: str) -> bool:
    block = context_sync_block(tenant_config)
    sources = block.get("sources")
    if not isinstance(sources, dict):
        return True
    return bool(sources.get(source, True))


def gmail_lookback_days(tenant_config: dict[str, Any] | None) -> int:
    block = context_sync_block(tenant_config)
    try:
        return max(1, min(90, int(block.get("gmail_lookback_days", 30))))
    except (TypeError, ValueError):
        return 30


def rollup_enabled(tenant_config: dict[str, Any] | None, *, plan: str = "") -> bool:
    block = context_sync_block(tenant_config)
    if block.get("rollup_enabled") is True:
        return True
    return str(plan).lower() == "enterprise"


def inject_max_tokens(tenant_config: dict[str, Any] | None) -> int:
    block = context_sync_block(tenant_config)
    try:
        return max(500, min(16_000, int(block.get("inject_max_tokens", 4096))))
    except (TypeError, ValueError):
        return 4096
