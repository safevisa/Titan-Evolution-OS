"""GitHub OAuth for Context Sync."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

from app.core.config import settings
from app.integrations.oauth_flows import pack_oauth_state, public_api_base
from app.integrations.transport import integration_request

GITHUB_SCOPES = "read:user repo"


def _client_id() -> str:
    cid = (settings.github_oauth_client_id or "").strip()
    if not cid:
        raise ValueError("GitHub OAuth requires GITHUB_OAUTH_CLIENT_ID")
    return cid


def _client_secret() -> str:
    sec = (settings.github_oauth_client_secret or "").strip()
    if not sec:
        raise ValueError("GitHub OAuth requires GITHUB_OAUTH_CLIENT_SECRET")
    return sec


def github_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/github/callback"


def github_authorize_url(*, tenant_id: str) -> str:
    st = pack_oauth_state(tenant_id, "github")
    q = urlencode(
        {
            "client_id": _client_id(),
            "redirect_uri": github_oauth_redirect_uri(),
            "scope": GITHUB_SCOPES,
            "state": st,
        }
    )
    return f"https://github.com/login/oauth/authorize?{q}"


async def github_exchange_code(code: str) -> dict[str, Any]:
    r = await integration_request(
        "POST",
        "https://github.com/login/oauth/access_token",
        provider="github_oauth",
        timeout=30.0,
        headers={"Accept": "application/json"},
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "code": code,
            "redirect_uri": github_oauth_redirect_uri(),
        },
    )
    data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "github_token_failed"))))
    return data
