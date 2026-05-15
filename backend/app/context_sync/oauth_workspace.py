"""Google Workspace OAuth (Gmail + Calendar)."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from app.core.config import settings
from app.integrations.oauth_flows import pack_oauth_state, public_api_base
from app.integrations.transport import integration_request

GOOGLE_WORKSPACE_SCOPES = (
    "https://www.googleapis.com/auth/gmail.readonly "
    "https://www.googleapis.com/auth/calendar.readonly "
    "openid email profile"
)


def _client_id() -> str:
    cid = (settings.google_workspace_oauth_client_id or settings.google_oauth_client_id or "").strip()
    if not cid:
        raise ValueError("Google Workspace OAuth requires GOOGLE_WORKSPACE_OAUTH_CLIENT_ID or GOOGLE_OAUTH_CLIENT_ID")
    return cid


def _client_secret() -> str:
    sec = (settings.google_workspace_oauth_client_secret or settings.google_oauth_client_secret or "").strip()
    if not sec:
        raise ValueError(
            "Google Workspace OAuth requires GOOGLE_WORKSPACE_OAUTH_CLIENT_SECRET or GOOGLE_OAUTH_CLIENT_SECRET"
        )
    return sec


def google_workspace_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/google-workspace/callback"


def google_workspace_authorize_url(*, tenant_id: str) -> str:
    st = pack_oauth_state(tenant_id, "google_workspace")
    q = urlencode(
        {
            "client_id": _client_id(),
            "redirect_uri": google_workspace_redirect_uri(),
            "response_type": "code",
            "scope": GOOGLE_WORKSPACE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": st,
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{q}"


async def google_workspace_exchange_code(code: str) -> dict[str, Any]:
    r = await integration_request(
        "POST",
        "https://oauth2.googleapis.com/token",
        provider="google_workspace_oauth",
        timeout=30.0,
        data={
            "code": code,
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri": google_workspace_redirect_uri(),
            "grant_type": "authorization_code",
        },
    )
    data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "google_workspace_token_failed"))))
    return data


async def google_workspace_refresh_access_token(refresh_token: str) -> dict[str, Any]:
    r = await integration_request(
        "POST",
        "https://oauth2.googleapis.com/token",
        provider="google_workspace_oauth",
        timeout=30.0,
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        },
    )
    data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "google_workspace_refresh_failed"))))
    return data
