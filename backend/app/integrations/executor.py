from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.integrations.builtins_dispatch import run_builtin_capability
from app.integrations.capability_audit_repo import (
    append_audit_log,
    idempotency_mark_failed,
    idempotency_mark_succeeded,
    idempotency_try_begin,
)
from app.integrations.capability_invoke import invoke_external_capability
from app.integrations.capability_metering import (
    check_capability_rate_limit,
    record_capability_metering,
)
from app.integrations.catalog import CAPABILITIES, get_capability, resolve_capability
from app.integrations.connections_repo import list_providers_for_tenant
from app.integrations.grants import (
    can_execute_capability,
    has_user_connection,
    oauth_server_env_ready,
    server_env_ready,
    tenant_allows_capability,
)
from app.integrations.param_norm import (
    redact_params_snapshot,
    split_control_params,
    summarize_capability_result,
)
from app.models.domain import Tenant

_MAX_IDEM_JSON = 110_000


def _idempotency_storage_blob(result: dict[str, Any]) -> dict[str, Any]:
    """Persist minimal replay payload; cap size for Postgres JSONB."""
    blob: dict[str, Any] = {
        "ok": bool(result.get("ok")),
        "error": result.get("error"),
        "data": result.get("data"),
    }
    raw = json.dumps(blob, default=str, ensure_ascii=False)
    if len(raw.encode("utf-8")) > _MAX_IDEM_JSON:
        return {
            "ok": bool(result.get("ok")),
            "error": result.get("error"),
            "data": None,
            "_truncated": True,
        }
    return blob


async def _run_capability_core(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    capability_id: str,
    clean_params: dict[str, Any],
) -> dict[str, Any]:
    cap = get_capability(capability_id)
    if cap is None:
        return {"ok": False, "capability_id": capability_id, "error": "unknown_capability"}

    tenant = await session.get(Tenant, tenant_id)
    cfg = tenant.config if tenant and isinstance(tenant.config, dict) else None
    provs = await list_providers_for_tenant(session, tenant_id)
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
        data = await run_builtin_capability("apollo_search", clean_params)
        return {"ok": True, "capability_id": capability_id, "data": data}

    if cap.id == "resend_email":
        data = await run_builtin_capability("resend_email", clean_params)
        return {"ok": True, "capability_id": capability_id, "data": data}

    from app.context_sync.capability_handlers import try_context_sync_capability
    from app.computer_use.capability_handlers import try_computer_use_capability

    handled, teo_result = await try_context_sync_capability(
        session, tenant_id=tenant_id, capability_id=capability_id, clean_params=clean_params
    )
    if handled and teo_result is not None:
        return teo_result
    handled, teo_result = await try_computer_use_capability(
        session, tenant_id=tenant_id, capability_id=capability_id, clean_params=clean_params
    )
    if handled and teo_result is not None:
        return teo_result

    if cap.connection_provider_any and has_user_connection(cap, provs):
        inner = await invoke_external_capability(capability_id, clean_params, session, tenant_id)
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


async def _finalize_audit_and_idempotency(
    *,
    tenant_id: UUID,
    capability_id: str,
    capability_ref: str,
    cap_meta: Any,
    clean_params: dict[str, Any],
    actor: str | None,
    correlation_id: str | None,
    idempotency_key: str | None,
    result: dict[str, Any],
) -> None:
    req_snap = redact_params_snapshot(clean_params)
    res_snap = summarize_capability_result(result)
    ok = bool(result.get("ok"))
    err = str(result.get("error")) if result.get("error") else None

    async with AsyncSessionLocal() as session:
        async with session.begin():
            await append_audit_log(
                session,
                tenant_id=tenant_id,
                capability_id=capability_ref[:160],
                ok=ok,
                actor=actor,
                correlation_id=correlation_id,
                request_summary=req_snap,
                error=err,
                result_summary=res_snap,
            )
            if ok and cap_meta is not None:
                await record_capability_metering(
                    session,
                    tenant_id=tenant_id,
                    capability_ref=capability_ref,
                    cap=cap_meta,
                    ok=True,
                )
            if idempotency_key:
                if ok:
                    await idempotency_mark_succeeded(
                        session,
                        tenant_id=tenant_id,
                        idempotency_key=idempotency_key,
                        result_ok=ok,
                        result_for_storage=_idempotency_storage_blob(result),
                    )
                else:
                    await idempotency_mark_failed(
                        session,
                        tenant_id=tenant_id,
                        idempotency_key=idempotency_key,
                    )


async def execute_capability(
    capability_id: str,
    params: dict[str, Any],
    *,
    tenant_id: str,
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """
    Global entry: run one capability after tenant policy + readiness checks.
    Optional control fields on params (stripped before execution):
      _idempotency_key, _correlation_id, _actor
    """
    clean, idempotency_key, correlation_id, actor = split_control_params(params)
    tid = UUID(str(tenant_id))

    resolved = resolve_capability(capability_id)
    if resolved is None:
        async with AsyncSessionLocal() as s_audit:
            async with s_audit.begin():
                await append_audit_log(
                    s_audit,
                    tenant_id=tid,
                    capability_id=capability_id[:160],
                    ok=False,
                    actor=actor,
                    correlation_id=correlation_id,
                    request_summary=redact_params_snapshot(clean),
                    error="unknown_capability",
                    result_summary=None,
                )
        return {"ok": False, "capability_id": capability_id, "error": "unknown_capability"}

    cap_meta = resolved.capability
    cap_ref = resolved.ref
    canonical_id = resolved.canonical_id

    async with AsyncSessionLocal() as s_plan:
        tenant = await s_plan.get(Tenant, tid)
        plan = str(tenant.plan) if tenant and tenant.plan else "starter"

    allowed, _remaining = await check_capability_rate_limit(
        tid, cap_ref, plan=plan, cap=cap_meta
    )
    if not allowed:
        blocked = {
            "ok": False,
            "capability_id": canonical_id,
            "capability_ref": cap_ref,
            "error": "capability_rate_limited",
        }
        await _finalize_audit_and_idempotency(
            tenant_id=tid,
            capability_id=canonical_id,
            capability_ref=cap_ref,
            cap_meta=cap_meta,
            clean_params=clean,
            actor=actor,
            correlation_id=correlation_id,
            idempotency_key=None,
            result=blocked,
        )
        return blocked

    if idempotency_key:
        async with AsyncSessionLocal() as s_claim:
            async with s_claim.begin():
                outcome, replay = await idempotency_try_begin(
                    s_claim,
                    tenant_id=tid,
                    idempotency_key=idempotency_key,
                    capability_id=cap_ref,
                )
        if outcome == "replay" and replay is not None:
            async with AsyncSessionLocal() as s_audit:
                async with s_audit.begin():
                    await append_audit_log(
                        s_audit,
                        tenant_id=tid,
                        capability_id=cap_ref,
                        ok=bool(replay.get("ok")),
                        actor=actor,
                        correlation_id=correlation_id,
                        request_summary=redact_params_snapshot(clean),
                        error=None,
                        result_summary={"idempotent_replay": True},
                    )
            return replay
        if outcome == "conflict":
            async with AsyncSessionLocal() as s_audit:
                async with s_audit.begin():
                    await append_audit_log(
                        s_audit,
                        tenant_id=tid,
                        capability_id=cap_ref,
                        ok=False,
                        actor=actor,
                        correlation_id=correlation_id,
                        request_summary=redact_params_snapshot(clean),
                        error="idempotency_conflict",
                        result_summary=None,
                    )
            return {
                "ok": False,
                "capability_id": canonical_id,
                "capability_ref": cap_ref,
                "error": "idempotency_conflict",
            }

    try:
        if db is not None:
            result = await _run_capability_core(
                db, tenant_id=tid, capability_id=canonical_id, clean_params=clean
            )
        else:
            async with AsyncSessionLocal() as session:
                async with session.begin():
                    result = await _run_capability_core(
                        session, tenant_id=tid, capability_id=canonical_id, clean_params=clean
                    )

        result.setdefault("capability_ref", cap_ref)
        result["capability_id"] = canonical_id

        await _finalize_audit_and_idempotency(
            tenant_id=tid,
            capability_id=canonical_id,
            capability_ref=cap_ref,
            cap_meta=cap_meta,
            clean_params=clean,
            actor=actor,
            correlation_id=correlation_id,
            idempotency_key=idempotency_key,
            result=result,
        )
        return result
    except Exception as exc:
        if idempotency_key:
            async with AsyncSessionLocal() as s_fail:
                async with s_fail.begin():
                    await idempotency_mark_failed(
                        s_fail,
                        tenant_id=tid,
                        idempotency_key=idempotency_key,
                    )
        err_name = type(exc).__name__
        async with AsyncSessionLocal() as s_audit:
            async with s_audit.begin():
                await append_audit_log(
                    s_audit,
                    tenant_id=tid,
                    capability_id=cap_ref[:160],
                    ok=False,
                    actor=actor,
                    correlation_id=correlation_id,
                    request_summary=redact_params_snapshot(clean),
                    error=f"exception:{err_name}",
                    result_summary=None,
                )
        raise


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
        cap_ref = f"{cap.id}@{cap.version}" if cap.version else cap.id
        rows.append(
            {
                "id": cap.id,
                "capability_ref": cap_ref,
                "version": cap.version,
                "quota_per_minute": cap.quota_per_minute,
                "bill_unit_usd": cap.bill_unit_usd,
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
