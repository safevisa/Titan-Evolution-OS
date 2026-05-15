"""OAuth authorize URLs and token exchange for Slack, X (Twitter), and LinkedIn."""
from __future__ import annotations

import base64
import hashlib
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.integrations.token_vault import decrypt_json, encrypt_json

SLACK_BOT_SCOPES = "chat:write,channels:read,groups:read,im:read,im:write,mpim:write"
TWITTER_SCOPES = "tweet.read tweet.write users.read offline.access"
LINKEDIN_SCOPES = "openid profile email w_member_social"


def public_api_base() -> str:
    raw = (settings.titan_api_public_base_url or "").strip().rstrip("/")
    if not raw:
        raise ValueError("Set TITAN_API_PUBLIC_BASE_URL to your public API origin (https://...)")
    return raw


def slack_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/slack/callback"


def twitter_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/twitter/callback"


def linkedin_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/linkedin/callback"


def pack_oauth_state(tenant_id: str, provider: str, **extra: Any) -> str:
    payload: dict[str, Any] = {"t": tenant_id, "p": provider, "ts": time.time()}
    payload.update(extra)
    return encrypt_json(payload)


def unpack_oauth_state(state: str) -> dict[str, Any]:
    data = decrypt_json(state)
    if time.time() - float(data.get("ts", 0)) > 900:
        raise ValueError("oauth state expired")
    return data


def slack_authorize_url(*, tenant_id: str) -> str:
    if not settings.slack_client_id or not settings.slack_client_secret:
        raise ValueError("Slack OAuth requires SLACK_CLIENT_ID and SLACK_CLIENT_SECRET")
    st = pack_oauth_state(tenant_id, "slack")
    q = urlencode(
        {
            "client_id": settings.slack_client_id,
            "scope": SLACK_BOT_SCOPES,
            "redirect_uri": slack_oauth_redirect_uri(),
            "state": st,
        }
    )
    return f"https://slack.com/oauth/v2/authorize?{q}"


def twitter_authorize_url(*, tenant_id: str) -> str:
    if not settings.twitter_client_id or not settings.twitter_client_secret:
        raise ValueError("Twitter OAuth requires TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET")
    code_verifier = secrets.token_urlsafe(48)
    challenge_bytes = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_bytes).decode("ascii").rstrip("=")
    st = pack_oauth_state(tenant_id, "twitter", cv=code_verifier)
    q = urlencode(
        {
            "response_type": "code",
            "client_id": settings.twitter_client_id,
            "redirect_uri": twitter_oauth_redirect_uri(),
            "scope": TWITTER_SCOPES,
            "state": st,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"https://twitter.com/i/oauth2/authorize?{q}"


def linkedin_authorize_url(*, tenant_id: str) -> str:
    if not settings.linkedin_client_id or not settings.linkedin_client_secret:
        raise ValueError("LinkedIn OAuth requires LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET")
    st = pack_oauth_state(tenant_id, "linkedin")
    q = urlencode(
        {
            "response_type": "code",
            "client_id": settings.linkedin_client_id,
            "redirect_uri": linkedin_oauth_redirect_uri(),
            "scope": LINKEDIN_SCOPES,
            "state": st,
        }
    )
    return f"https://www.linkedin.com/oauth/v2/authorization?{q}"


async def exchange_slack_oauth_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": slack_oauth_redirect_uri(),
            },
        )
        data = r.json()
    if not data.get("ok"):
        raise ValueError(data.get("error", "slack_oauth_failed"))
    return data


async def exchange_twitter_oauth_code(code: str, code_verifier: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.twitter.com/2/oauth2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=(settings.twitter_client_id or "", settings.twitter_client_secret or ""),
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": twitter_oauth_redirect_uri(),
                "code_verifier": code_verifier,
                "client_id": settings.twitter_client_id,
            },
        )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(data.get("error_description") or data.get("error") or "twitter_token_failed")
    return data


async def exchange_linkedin_oauth_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": linkedin_oauth_redirect_uri(),
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret,
            },
        )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text}
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(data.get("error_description") or data.get("error") or "linkedin_token_failed")
    return data


async def fetch_linkedin_person_urn(access_token: str) -> tuple[str, dict[str, Any]]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = r.json()
    if r.status_code != 200:
        raise ValueError("linkedin_userinfo_failed")
    sub = str(data.get("sub", "")).strip()
    if not sub:
        raise ValueError("linkedin_userinfo_missing_sub")
    author = sub if sub.startswith("urn:li:person:") else f"urn:li:person:{sub}"
    return author, data
