"""Orchestrate per-tenant Context Sync (gmail → gcal → github)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.context_sync.config_helpers import (
    context_sync_enabled,
    gmail_lookback_days,
    source_enabled,
)
from app.context_sync.fetchers.github import fetch_github_items
from app.context_sync.fetchers.gmail import fetch_gmail_items
from app.context_sync.fetchers.google_calendar import fetch_calendar_items
from app.context_sync.pipeline import ingest_items
from app.context_sync.sync_state_repo import get_sync_state, upsert_sync_state
from app.integrations.connection_tokens import get_connection_secret
from app.integrations.providers import PROVIDER_GITHUB_OAUTH, PROVIDER_GOOGLE_WORKSPACE_OAUTH
from app.models.domain import Tenant

SyncSource = Literal["gmail", "gcal", "github"]
SYNC_PROVIDER_WORKSPACE = "google_workspace"
SYNC_PROVIDER_GITHUB = "github"


async def _run_gmail(
    session: AsyncSession,
    tenant: Tenant,
) -> dict[str, Any]:
    if not source_enabled(tenant.config, "gmail"):
        return {"ok": True, "skipped": 0, "ingested": 0, "message": "source_disabled"}
    secret = await get_connection_secret(session, tenant.id, PROVIDER_GOOGLE_WORKSPACE_OAUTH)
    if not secret or not secret.get("access_token"):
        return {"ok": False, "error": "not_connected", "ingested": 0, "skipped": 0}

    state = await get_sync_state(session, tenant.id, SYNC_PROVIDER_WORKSPACE)
    cursor = dict(state.cursor_json) if state else {}
    items, new_cursor, err = await fetch_gmail_items(
        str(secret["access_token"]),
        lookback_days=gmail_lookback_days(tenant.config),
        cursor_json=cursor,
    )
    if err:
        await upsert_sync_state(
            session,
            tenant_id=tenant.id,
            provider=SYNC_PROVIDER_WORKSPACE,
            cursor_json=new_cursor,
            last_error=err,
        )
        return {"ok": False, "error": err, "ingested": 0, "skipped": 0}

    stats = await ingest_items(session, tenant_id=tenant.id, items=items)
    await upsert_sync_state(
        session,
        tenant_id=tenant.id,
        provider=SYNC_PROVIDER_WORKSPACE,
        cursor_json=new_cursor,
        last_success_at=datetime.now(timezone.utc),
        last_error=None if not stats.errors else "; ".join(stats.errors[:3]),
    )
    return {
        "ok": True,
        "ingested": stats.ingested,
        "skipped": stats.skipped,
        "errors": stats.errors,
    }


async def _run_gcal(
    session: AsyncSession,
    tenant: Tenant,
) -> dict[str, Any]:
    if not source_enabled(tenant.config, "gcal"):
        return {"ok": True, "skipped": 0, "ingested": 0, "message": "source_disabled"}
    secret = await get_connection_secret(session, tenant.id, PROVIDER_GOOGLE_WORKSPACE_OAUTH)
    if not secret or not secret.get("access_token"):
        return {"ok": False, "error": "not_connected", "ingested": 0, "skipped": 0}

    state = await get_sync_state(session, tenant.id, SYNC_PROVIDER_WORKSPACE)
    cursor = dict(state.cursor_json) if state else {}
    items, new_cursor, err = await fetch_calendar_items(
        str(secret["access_token"]),
        cursor_json=cursor,
    )
    if err:
        await upsert_sync_state(
            session,
            tenant_id=tenant.id,
            provider=SYNC_PROVIDER_WORKSPACE,
            cursor_json=new_cursor,
            last_error=err,
        )
        return {"ok": False, "error": err, "ingested": 0, "skipped": 0}

    stats = await ingest_items(session, tenant_id=tenant.id, items=items)
    await upsert_sync_state(
        session,
        tenant_id=tenant.id,
        provider=SYNC_PROVIDER_WORKSPACE,
        cursor_json=new_cursor,
        last_success_at=datetime.now(timezone.utc),
        last_error=None if not stats.errors else "; ".join(stats.errors[:3]),
    )
    return {
        "ok": True,
        "ingested": stats.ingested,
        "skipped": stats.skipped,
        "errors": stats.errors,
    }


async def _run_github(
    session: AsyncSession,
    tenant: Tenant,
) -> dict[str, Any]:
    if not source_enabled(tenant.config, "github"):
        return {"ok": True, "skipped": 0, "ingested": 0, "message": "source_disabled"}
    secret = await get_connection_secret(session, tenant.id, PROVIDER_GITHUB_OAUTH)
    if not secret or not secret.get("access_token"):
        return {"ok": False, "error": "not_connected", "ingested": 0, "skipped": 0}

    state = await get_sync_state(session, tenant.id, SYNC_PROVIDER_GITHUB)
    cursor = dict(state.cursor_json) if state else {}
    items, new_cursor, err = await fetch_github_items(
        str(secret["access_token"]),
        cursor_json=cursor,
    )
    if err:
        await upsert_sync_state(
            session,
            tenant_id=tenant.id,
            provider=SYNC_PROVIDER_GITHUB,
            cursor_json=new_cursor,
            last_error=err,
        )
        return {"ok": False, "error": err, "ingested": 0, "skipped": 0}

    stats = await ingest_items(session, tenant_id=tenant.id, items=items)
    await upsert_sync_state(
        session,
        tenant_id=tenant.id,
        provider=SYNC_PROVIDER_GITHUB,
        cursor_json=new_cursor,
        last_success_at=datetime.now(timezone.utc),
        last_error=None if not stats.errors else "; ".join(stats.errors[:3]),
    )
    return {
        "ok": True,
        "ingested": stats.ingested,
        "skipped": stats.skipped,
        "errors": stats.errors,
    }


async def sync_tenant_sources(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    *,
    sources: list[SyncSource] | None = None,
) -> dict[str, Any]:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        return {"ok": False, "error": "tenant_not_found"}
    if not context_sync_enabled(tenant.config):
        return {"ok": False, "error": "context_sync_disabled"}

    want: list[SyncSource] = sources or ["gmail", "gcal", "github"]
    out: dict[str, Any] = {"ok": True, "data": {}}

    if "gmail" in want:
        out["data"]["gmail"] = await _run_gmail(session, tenant)
    if "gcal" in want:
        out["data"]["gcal"] = await _run_gcal(session, tenant)
    if "github" in want:
        out["data"]["github"] = await _run_github(session, tenant)

    if any(not v.get("ok", True) for v in out["data"].values() if isinstance(v, dict)):
        out["ok"] = False
    return out


async def build_sync_status(
    session: AsyncSession,
    tenant_id: uuid.UUID,
) -> dict[str, Any]:
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        return {"enabled": False, "error": "tenant_not_found"}

    ws_secret = await get_connection_secret(
        session, tenant_id, PROVIDER_GOOGLE_WORKSPACE_OAUTH, refresh_if_needed=False
    )
    gh_secret = await get_connection_secret(
        session, tenant_id, PROVIDER_GITHUB_OAUTH, refresh_if_needed=False
    )
    ws_state = await get_sync_state(session, tenant_id, SYNC_PROVIDER_WORKSPACE)
    gh_state = await get_sync_state(session, tenant_id, SYNC_PROVIDER_GITHUB)

    def _src(
        connected: bool,
        state_row,
        *,
        requires_workspace: bool,
    ) -> dict[str, Any]:
        if not connected:
            return {"connected": False, "status": "not_connected", "last_success_at": None, "last_error": None}
        err = state_row.last_error if state_row else None
        ok_at = state_row.last_success_at.isoformat() if state_row and state_row.last_success_at else None
        status = "ok" if ok_at and not err else ("error" if err else "pending")
        return {
            "connected": True,
            "status": status,
            "last_success_at": ok_at,
            "last_error": err,
            "requires": "google_workspace" if requires_workspace else "github",
        }

    ws_connected = bool(ws_secret and ws_secret.get("access_token"))
    gh_connected = bool(gh_secret and gh_secret.get("access_token"))

    return {
        "enabled": context_sync_enabled(tenant.config),
        "sources": {
            "gmail": _src(ws_connected, ws_state, requires_workspace=True),
            "gcal": _src(ws_connected, ws_state, requires_workspace=True),
            "github": _src(gh_connected, gh_state, requires_workspace=False),
        },
    }
