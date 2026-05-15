"""External capability catalog, per-tenant grants, webhook connections, and OAuth."""
from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.integrations.catalog import all_capability_ids
from app.integrations.connections_repo import (
    delete_connection,
    list_connections_public,
    list_providers_for_tenant,
    upsert_encrypted_payload,
)
from app.integrations.agent_capabilities import list_agent_capabilities
from app.integrations.agent_tool_bridge import capabilities_to_openai_tools
from app.integrations.capability_metering import list_capability_usage
from app.integrations.capability_packs import (
    capability_refs_to_grant_ids,
    get_capability_pack,
    list_capability_packs,
    merge_grant_ids,
)
from app.integrations.grants import enabled_capability_ids_explicit
from app.integrations.executor import capability_list_for_api, execute_capability
from app.integrations.oauth_token_refresh import attach_token_expiry
from app.integrations.grants import INTEGRATION_GRANTS_KEY
from app.integrations.credential_validate import validate_credential_payload
from app.integrations.oauth_extended import (
    facebook_authorize_url,
    facebook_exchange_code_for_user_token,
    facebook_long_lived_user_token,
    facebook_pick_page_and_ig,
    google_exchange_code,
    google_youtube_authorize_url,
    google_youtube_fetch_channel_id,
    reddit_authorize_url,
    reddit_exchange_code,
    weibo_authorize_url,
    weibo_exchange_code,
)
from app.integrations.oauth_flows import (
    exchange_linkedin_oauth_code,
    exchange_slack_oauth_code,
    exchange_twitter_oauth_code,
    fetch_linkedin_person_urn,
    linkedin_authorize_url,
    slack_authorize_url,
    twitter_authorize_url,
    unpack_oauth_state,
)
from app.context_sync.oauth_github import github_authorize_url, github_exchange_code, github_oauth_redirect_uri
from app.context_sync.oauth_workspace import (
    google_workspace_authorize_url,
    google_workspace_exchange_code,
    google_workspace_redirect_uri,
)
from app.context_sync.purge import SOURCE_BY_OAUTH, purge_for_oauth_provider
from app.context_sync.sync_service import SYNC_PROVIDER_GITHUB, SYNC_PROVIDER_WORKSPACE, build_sync_status
from app.context_sync.sync_state_repo import upsert_sync_state
from app.integrations.providers import (
    CREDENTIAL_PROVIDERS,
    PROVIDER_FACEBOOK_GRAPH_OAUTH,
    PROVIDER_GITHUB_OAUTH,
    PROVIDER_GOOGLE_WORKSPACE_OAUTH,
    PROVIDER_GOOGLE_YOUTUBE_OAUTH,
    PROVIDER_LINKEDIN_OAUTH,
    PROVIDER_REDDIT_OAUTH,
    PROVIDER_SLACK_OAUTH,
    PROVIDER_TWITTER_OAUTH,
    PROVIDER_WEIBO_OAUTH,
)
from app.integrations.token_vault import IntegrationVaultError
from app.integrations.webhook_validate import validate_webhook_for_provider
from app.models.domain import Tenant

router = APIRouter(prefix="/integrations", tags=["integrations"])

WebhookProvider = Literal[
    "discord_webhook",
    "slack_incoming_webhook",
    "feishu_webhook",
    "wechat_work_webhook",
]


class CredentialConnectionBody(BaseModel):
    provider: str = Field(..., min_length=4, max_length=64)
    payload: dict[str, Any] = Field(default_factory=dict)


class WebhookConnectionBody(BaseModel):
    provider: WebhookProvider
    webhook_url: str = Field(..., min_length=12, max_length=2048)

    @model_validator(mode="after")
    def validate_url(self) -> WebhookConnectionBody:
        self.webhook_url = validate_webhook_for_provider(self.provider, self.webhook_url)
        return self


class IntegrationGrantsBody(BaseModel):
    enabled_capability_ids: list[str] = Field(
        default_factory=list,
        description="Explicit allow-list. When empty list is sent, no capabilities are allowed by policy.",
    )


class ApplyCapabilityPackBody(BaseModel):
    pack_id: str = Field(..., min_length=2, max_length=64)
    merge: bool = Field(
        default=True,
        description="If true, union pack capabilities with existing grants; if false, replace grants with pack only.",
    )


class ExecuteCapabilityBody(BaseModel):
    capability_id: str = Field(..., min_length=2, max_length=160)
    params: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = Field(default=None, max_length=160)
    correlation_id: str | None = Field(default=None, max_length=128)
    actor: str | None = Field(default=None, max_length=256)


@router.get("/capabilities")
async def list_capabilities(
    tenant_id: UUID = Query(..., description="Tenant UUID to evaluate policy + readiness flags"),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    cfg = tenant.config if isinstance(tenant.config, dict) else None
    provs = await list_providers_for_tenant(db, tenant_id)
    return capability_list_for_api(cfg, provs)


@router.get("/tenants/{tenant_id}/agents/{role}/capabilities")
async def list_agent_role_capabilities(
    tenant_id: UUID,
    role: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    cfg = tenant.config if isinstance(tenant.config, dict) else None
    provs = await list_providers_for_tenant(db, tenant_id)
    caps = list_agent_capabilities(role=role, tenant_config=cfg, connection_providers=provs)
    tools, _name_map = capabilities_to_openai_tools(caps)
    return {
        "tenant_id": str(tenant_id),
        "role": role,
        "capabilities": caps,
        "openai_tools": tools,
    }


@router.get("/capability-packs")
async def list_capability_packs_http(
    role: str | None = Query(default=None, max_length=64),
) -> list[dict[str, Any]]:
    return list_capability_packs(role=role)


@router.get("/capability-packs/{pack_id}")
async def get_capability_pack_http(pack_id: str) -> dict[str, Any]:
    pack = get_capability_pack(pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="capability pack not found")
    return {
        "id": pack.id,
        "display_name": pack.display_name,
        "description": pack.description,
        "capability_refs": list(pack.capability_refs),
        "roles_hint": list(pack.roles_hint),
    }


@router.get("/tenants/{tenant_id}/capability-usage")
async def get_capability_usage_http(
    tenant_id: UUID,
    year: int | None = Query(default=None, ge=2020, le=2100),
    month: int | None = Query(default=None, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    rows = await list_capability_usage(db, tenant_id, year=year, month=month)
    return {"tenant_id": str(tenant_id), "usage": rows}


@router.post("/tenants/{tenant_id}/capabilities/execute")
async def execute_capability_http(
    tenant_id: UUID,
    body: ExecuteCapabilityBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    params = dict(body.params)
    if body.idempotency_key:
        params["_idempotency_key"] = body.idempotency_key
    if body.correlation_id:
        params["_correlation_id"] = body.correlation_id
    if body.actor:
        params["_actor"] = body.actor
    result = await execute_capability(
        body.capability_id,
        params,
        tenant_id=str(tenant_id),
        db=db,
    )
    await db.commit()
    return result


@router.post("/tenants/{tenant_id}/grants/apply-pack", response_model=dict[str, Any])
async def apply_capability_pack_to_grants(
    tenant_id: UUID,
    body: ApplyCapabilityPackBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """One-click: enable all capabilities from a preset pack on the tenant allow-list."""
    pack = get_capability_pack(body.pack_id)
    if pack is None:
        raise HTTPException(status_code=404, detail="capability pack not found")

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    pack_ids = capability_refs_to_grant_ids(pack.capability_refs)
    if not pack_ids:
        raise HTTPException(status_code=400, detail="pack has no resolvable capabilities")

    cfg = tenant.config if isinstance(tenant.config, dict) else {}
    current = enabled_capability_ids_explicit(cfg)
    merged_ids = merge_grant_ids(current, pack_ids, merge=body.merge)

    unknown = set(merged_ids) - all_capability_ids()
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown capability ids after merge: {sorted(unknown)}",
        )

    merged = dict(cfg)
    block = dict(merged.get(INTEGRATION_GRANTS_KEY) or {})
    block["enabled_capability_ids"] = merged_ids
    merged[INTEGRATION_GRANTS_KEY] = block
    tenant.config = merged
    await db.commit()
    await db.refresh(tenant)

    provs = await list_providers_for_tenant(db, tenant_id)
    return {
        "ok": True,
        "tenant_id": str(tenant_id),
        "pack_id": pack.id,
        "added_from_pack": pack_ids,
        "merge": body.merge,
        INTEGRATION_GRANTS_KEY: tenant.config.get(INTEGRATION_GRANTS_KEY),
        "capabilities": capability_list_for_api(
            tenant.config if isinstance(tenant.config, dict) else None,
            provs,
        ),
    }


@router.patch("/tenants/{tenant_id}/grants", response_model=dict[str, Any])
async def update_integration_grants(
    tenant_id: UUID,
    body: IntegrationGrantsBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    unknown = set(body.enabled_capability_ids) - all_capability_ids()
    if unknown:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown capability ids: {sorted(unknown)}",
        )

    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")

    merged = dict(tenant.config or {})
    block = dict(merged.get(INTEGRATION_GRANTS_KEY) or {})
    block["enabled_capability_ids"] = list(dict.fromkeys(body.enabled_capability_ids))
    merged[INTEGRATION_GRANTS_KEY] = block
    tenant.config = merged
    await db.commit()
    await db.refresh(tenant)

    provs = await list_providers_for_tenant(db, tenant_id)
    return {
        "tenant_id": str(tenant_id),
        INTEGRATION_GRANTS_KEY: tenant.config.get(INTEGRATION_GRANTS_KEY),
        "capabilities": capability_list_for_api(
            tenant.config if isinstance(tenant.config, dict) else None,
            provs,
        ),
    }


@router.get("/tenants/{tenant_id}/connections")
async def get_connections(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return await list_connections_public(db, tenant_id)


@router.post("/tenants/{tenant_id}/connections/webhook")
async def add_webhook_connection(
    tenant_id: UUID,
    body: WebhookConnectionBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        await upsert_encrypted_payload(
            db,
            tenant_id,
            body.provider,
            payload={"webhook_url": body.webhook_url},
            meta={"kind": "webhook"},
        )
        await db.commit()
    except IntegrationVaultError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"ok": True, "provider": body.provider}


@router.post("/tenants/{tenant_id}/connections/credential")
async def add_credential_connection(
    tenant_id: UUID,
    body: CredentialConnectionBody,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    if body.provider not in CREDENTIAL_PROVIDERS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown credential provider (allowed: {sorted(CREDENTIAL_PROVIDERS)})",
        )
    try:
        clean = validate_credential_payload(body.provider, body.payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    try:
        await upsert_encrypted_payload(
            db,
            tenant_id,
            body.provider,
            payload=clean,
            meta={"kind": "credential"},
        )
        await db.commit()
    except IntegrationVaultError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    return {"ok": True, "provider": body.provider}


@router.delete("/tenants/{tenant_id}/connections/{provider}")
async def remove_connection(
    tenant_id: UUID,
    provider: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    tenant = await db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    ok = await delete_connection(db, tenant_id, provider)
    if not ok:
        raise HTTPException(status_code=404, detail="connection not found")
    purged: dict[str, int] = {}
    if provider in SOURCE_BY_OAUTH:
        purged = await purge_for_oauth_provider(db, tenant_id, provider)
    await db.commit()
    return {"ok": True, "deleted": provider, "purged": purged}


# --- OAuth (browser redirect) -------------------------------------------------


def _html_ok(title: str, body: str) -> HTMLResponse:
    return HTMLResponse(
        f"<html><head><meta charset=\"utf-8\"/><title>{title}</title></head>"
        f"<body><p>{body}</p><p>You can close this window.</p></body></html>"
    )


def _html_err(msg: str, status: int = 400) -> HTMLResponse:
    return HTMLResponse(
        f"<html><head><meta charset=\"utf-8\"/></head><body><p>Authorization failed: {msg}</p></body></html>",
        status_code=status,
    )


@router.get("/oauth/slack/start")
async def oauth_slack_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = slack_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/slack/callback", response_class=HTMLResponse)
async def oauth_slack_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "slack":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await exchange_slack_oauth_code(code)
        token = str(data.get("access_token", ""))
        if not token:
            return _html_err("slack token missing")
        team = data.get("team") or {}
        meta = {
            "slack_team_id": team.get("id"),
            "slack_team_name": team.get("name"),
            "bot_user_id": data.get("bot_user_id"),
        }
        await upsert_encrypted_payload(
            db, tid, PROVIDER_SLACK_OAUTH, payload={"access_token": token}, meta=meta
        )
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("Slack connected", "Slack workspace connected successfully.")


@router.get("/oauth/twitter/start")
async def oauth_twitter_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = twitter_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/twitter/callback", response_class=HTMLResponse)
async def oauth_twitter_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "twitter":
            return _html_err("invalid state provider")
        cv = str(st.get("cv", ""))
        if not cv:
            return _html_err("missing pkce verifier in state")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await exchange_twitter_oauth_code(code, cv)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("twitter token missing")
        meta = {"twitter_token_type": data.get("token_type", "bearer")}
        secret = attach_token_expiry(
            {
                "access_token": at,
                "refresh_token": str(data.get("refresh_token") or ""),
            },
            data,
        )
        await upsert_encrypted_payload(db, tid, PROVIDER_TWITTER_OAUTH, payload=secret, meta=meta)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("X connected", "X (Twitter) account connected successfully.")


@router.get("/oauth/linkedin/start")
async def oauth_linkedin_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = linkedin_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/linkedin/callback", response_class=HTMLResponse)
async def oauth_linkedin_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error_description or error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "linkedin":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await exchange_linkedin_oauth_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("linkedin token missing")
        author, userinfo = await fetch_linkedin_person_urn(at)
        meta = {
            "linkedin_person_urn": author,
            "linkedin_name": userinfo.get("name"),
        }
        secret = attach_token_expiry(
            {
                "access_token": at,
                "refresh_token": str(data.get("refresh_token") or ""),
            },
            data,
        )
        await upsert_encrypted_payload(db, tid, PROVIDER_LINKEDIN_OAUTH, payload=secret, meta=meta)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("LinkedIn connected", "LinkedIn member account connected successfully.")


@router.get("/oauth/facebook/start")
async def oauth_facebook_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = facebook_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/facebook/callback", response_class=HTMLResponse)
async def oauth_facebook_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error_description or error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "facebook":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        short_t = await facebook_exchange_code_for_user_token(code)
        long_user = await facebook_long_lived_user_token(short_t)
        page_token, page_id, ig_id = await facebook_pick_page_and_ig(long_user)
        meta: dict[str, Any] = {
            "facebook_page_id": page_id,
            "instagram_business_account_id": ig_id,
        }
        await upsert_encrypted_payload(
            db,
            tid,
            PROVIDER_FACEBOOK_GRAPH_OAUTH,
            payload={"page_access_token": page_token},
            meta=meta,
        )
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("Facebook connected", "Facebook Page (and Instagram if linked) connected.")


@router.get("/oauth/weibo/start")
async def oauth_weibo_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = weibo_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/weibo/callback", response_class=HTMLResponse)
async def oauth_weibo_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "weibo":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await weibo_exchange_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("weibo token missing")
        uid = str(data.get("uid", ""))
        meta = {"weibo_uid": uid}
        secret = {"access_token": at}
        await upsert_encrypted_payload(db, tid, PROVIDER_WEIBO_OAUTH, payload=secret, meta=meta)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("Weibo connected", "Weibo account connected successfully.")


@router.get("/oauth/reddit/start")
async def oauth_reddit_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = reddit_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/reddit/callback", response_class=HTMLResponse)
async def oauth_reddit_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "reddit":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await reddit_exchange_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("reddit token missing")
        secret = attach_token_expiry(
            {
                "access_token": at,
                "refresh_token": str(data.get("refresh_token") or ""),
            },
            data,
        )
        meta = {"reddit_token_type": data.get("token_type", "bearer")}
        await upsert_encrypted_payload(db, tid, PROVIDER_REDDIT_OAUTH, payload=secret, meta=meta)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("Reddit connected", "Reddit account connected successfully.")


@router.get("/oauth/google-youtube/start")
async def oauth_google_youtube_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = google_youtube_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/google-youtube/callback", response_class=HTMLResponse)
async def oauth_google_youtube_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error_description or error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "google_youtube":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await google_exchange_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("google token missing")
        ch = await google_youtube_fetch_channel_id(at)
        secret = attach_token_expiry(
            {
                "access_token": at,
                "refresh_token": str(data.get("refresh_token") or ""),
            },
            data,
        )
        meta = {"youtube_channel_id": ch}
        await upsert_encrypted_payload(db, tid, PROVIDER_GOOGLE_YOUTUBE_OAUTH, payload=secret, meta=meta)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("YouTube connected", "YouTube channel connected for commenting API.")


@router.get("/oauth/google-workspace/start")
async def oauth_google_workspace_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = google_workspace_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/google-workspace/callback", response_class=HTMLResponse)
async def oauth_google_workspace_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error_description or error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "google_workspace":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await google_workspace_exchange_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("google token missing")
        secret = attach_token_expiry(
            {
                "access_token": at,
                "refresh_token": str(data.get("refresh_token") or ""),
            },
            data,
        )
        scope = data.get("scope")
        if isinstance(scope, str) and scope.strip():
            secret["scopes"] = scope.split()
        await upsert_encrypted_payload(db, tid, PROVIDER_GOOGLE_WORKSPACE_OAUTH, payload=secret, meta={})
        await upsert_sync_state(db, tenant_id=tid, provider=SYNC_PROVIDER_WORKSPACE, enabled=True)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok(
        "Google Workspace connected",
        f"Gmail and Calendar connected. Redirect URI: {google_workspace_redirect_uri()}",
    )


@router.get("/oauth/github/start")
async def oauth_github_start(
    tenant_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    try:
        url = github_authorize_url(tenant_id=str(tenant_id))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return RedirectResponse(url, status_code=302)


@router.get("/oauth/github/callback", response_class=HTMLResponse)
async def oauth_github_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
    error_description: str = Query(""),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    if error:
        return _html_err(error_description or error)
    if not code or not state:
        return _html_err("missing code or state")
    try:
        st = unpack_oauth_state(state)
        if st.get("p") != "github":
            return _html_err("invalid state provider")
        tid = UUID(str(st["t"]))
        if await db.get(Tenant, tid) is None:
            return _html_err("tenant not found", 404)
        data = await github_exchange_code(code)
        at = str(data.get("access_token", ""))
        if not at:
            return _html_err("github token missing")
        secret = attach_token_expiry({"access_token": at}, data)
        await upsert_encrypted_payload(db, tid, PROVIDER_GITHUB_OAUTH, payload=secret, meta={})
        await upsert_sync_state(db, tenant_id=tid, provider=SYNC_PROVIDER_GITHUB, enabled=True)
        await db.commit()
    except (ValueError, KeyError, IntegrationVaultError) as e:
        await db.rollback()
        return _html_err(str(e))
    return _html_ok("GitHub connected", f"GitHub connected. Redirect URI: {github_oauth_redirect_uri()}")


@router.get("/tenants/{tenant_id}/sync-status")
async def tenant_sync_status(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    return await build_sync_status(db, tenant_id)


class SyncTriggerBody(BaseModel):
    sources: list[str] | None = Field(
        default=None,
        description="Optional subset: gmail, gcal, github",
    )


@router.post("/tenants/{tenant_id}/sync/trigger")
async def tenant_sync_trigger(
    tenant_id: UUID,
    body: SyncTriggerBody | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    if await db.get(Tenant, tenant_id) is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    params: dict[str, Any] = {}
    if body and body.sources:
        params["sources"] = body.sources
    params["_actor"] = "api:sync_trigger"
    result = await execute_capability(
        "context_sync_run",
        params,
        tenant_id=str(tenant_id),
        db=db,
    )
    await db.commit()
    return result
