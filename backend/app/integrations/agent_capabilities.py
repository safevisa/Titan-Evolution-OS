"""Capabilities visible to an agent role for a tenant (policy + connection + role hint)."""
from __future__ import annotations

from typing import Any

from app.integrations.catalog import CAPABILITIES, get_capability
from app.integrations.grants import can_execute_capability, tenant_allows_capability


def capability_visible_to_role(cap_id: str, role: str) -> bool:
    cap = get_capability(cap_id)
    if cap is None:
        return False
    if not cap.roles_hint:
        return True
    return role in cap.roles_hint


def list_agent_capabilities(
    *,
    role: str,
    tenant_config: dict[str, Any] | None,
    connection_providers: frozenset[str],
) -> list[dict[str, Any]]:
    """Subset of catalog entries an agent role may invoke (execute-time policy still applies)."""
    rows: list[dict[str, Any]] = []
    for cap in CAPABILITIES:
        if not capability_visible_to_role(cap.id, role):
            continue
        if not tenant_allows_capability(tenant_config, cap):
            continue
        can_run, reason = can_execute_capability(
            tenant_config, cap, connection_providers=connection_providers
        )
        cap_ref = f"{cap.id}@{cap.version}" if cap.version else cap.id
        rows.append(
            {
                "id": cap.id,
                "capability_ref": cap_ref,
                "version": cap.version,
                "display_name": cap.display_name,
                "category": cap.category,
                "description": cap.description,
                "can_execute_now": can_run,
                "execute_block_reason": None if can_run else reason,
            }
        )
    return rows
