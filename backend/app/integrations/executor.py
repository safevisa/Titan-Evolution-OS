from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.integrations.capability_invoke import invoke_external_capability
from app.integrations.catalog import CAPABILITIES, get_capability
from app.integrations.connections_repo import list_providers_for_tenant
from app.integrations.grants import (
    can_execute_capability,
    has_user_connection,
    oauth_server_env_ready,
    server_env_ready,
    tenant_allows_capability,
)
from app.models.domain import Tenant
from app.tools.tool_registry import run_tool


async def execute_capability(
    capability_id: str,
    params: dict[str, Any],
    *,
    tenant_id: str,
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """
    Run one capability after tenant policy + readiness checks.
    When `db` is None, opens a short-lived session to load tenant.config.
    """
    cap = get_capability(capability_id)
    if cap is None:
        return {"ok": False, "capability_id": capability_id, "error": "unknown_capability"}

    async def _run(session: AsyncSession) -> dict[str, Any]:
        tid = UUID(str(tenant_id))
        tenant = await session.get(Tenant, tid)
        cfg = tenant.config if tenant and isinstance(tenant.config, dict) else None
        provs = await list_providers_for_tenant(session, tid)
        allowed, reason = can_execute_capability(cfg, cap, connection_providers=provs)
        if not allowed:
            return {
                "ok": False,
                "capability_id": capability_id,
                "error": reason,
                "category": cap.category,
                "status": cap.status,
            }

        if cap.id == "apollo_search":
            data = await run_tool("apollo_search", **params)
            return {"ok": True, "capability_id": capability_id, "data": data}

        if cap.id == "resend_email":
            data = await run_tool("resend_email", **params)
            return {"ok": True, "capability_id": capability_id, "data": data}

        if cap.connection_provider_any and has_user_connection(cap, provs):
            inner = await invoke_external_capability(capability_id, params, session, tid)
            return {
                "ok": bool(inner.get("ok")),
                "capability_id": capability_id,
                "data": inner.get("data"),
                "error": inner.get("error"),
            }

        return {
            "ok": False,
            "capability_id": capability_id,
            "error": "internal_dispatch_missing",
        }

    if db is not None:
        return await _run(db)

    async with AsyncSessionLocal() as session:
        return await _run(session)


def capability_list_for_api(
    tenant_config: dict[str, Any] | None,
    connection_providers: frozenset[str],
) -> list[dict[str, Any]]:
    """Serialize catalog + flags for GET /integrations/capabilities."""
    rows: list[dict[str, Any]] = []
    for cap in CAPABILITIES:
        policy_ok = tenant_allows_capability(tenant_config, cap)
        ready_env = server_env_ready(cap) if cap.env_keys else False
        oauth_ready = oauth_server_env_ready(cap)
        user_conn = has_user_connection(cap, connection_providers) if cap.connection_provider_any else False
        can_run, reason = can_execute_capability(
            tenant_config, cap, connection_providers=connection_providers
        )
        rows.append(
            {
                "id": cap.id,
                "category": cap.category,
                "display_name": cap.display_name,
                "description": cap.description,
                "auth_mode": cap.auth_mode,
                "status": cap.status,
                "roles_hint": list(cap.roles_hint),
                "env_keys": list(cap.env_keys),
                "connection_provider_any": list(cap.connection_provider_any),
                "oauth_server_env_keys": list(cap.oauth_server_env_keys),
                "tenant_policy_allows": policy_ok,
                "server_env_configured": ready_env,
                "oauth_app_configured": oauth_ready,
                "user_connection_active": user_conn,
                "can_execute_now": can_run,
                "execute_block_reason": None if can_run else reason,
            }
        )
    return rows
