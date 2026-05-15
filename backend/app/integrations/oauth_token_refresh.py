"""Refresh OAuth access tokens and merge expiry metadata into connection payloads."""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlencode

from app.core.config import settings
from app.integrations.oauth_extended import google_refresh_access_token, reddit_refresh_access_token
from app.integrations.providers import (
    PROVIDER_GOOGLE_YOUTUBE_OAUTH,
    PROVIDER_LINKEDIN_OAUTH,
    PROVIDER_REDDIT_OAUTH,
    PROVIDER_TWITTER_OAUTH,
)
from app.integrations.transport import integration_request

_REFRESHABLE = frozenset(
    {
        PROVIDER_TWITTER_OAUTH,
        PROVIDER_LINKEDIN_OAUTH,
        PROVIDER_REDDIT_OAUTH,
        PROVIDER_GOOGLE_YOUTUBE_OAUTH,
    }
)


def oauth_providers_with_refresh() -> frozenset[str]:
    return _REFRESHABLE


def attach_token_expiry(payload: dict[str, Any], token_response: dict[str, Any]) -> dict[str, Any]:
    """Add expires_at unix timestamp from OAuth token response."""
    out = dict(payload)
    expires_in = token_response.get("expires_in")
    if expires_in is not None:
        try:
            sec = int(expires_in)
            out["expires_at"] = time.time() + max(sec - 120, 60)
        except (TypeError, ValueError):
            pass
    return out


def token_needs_refresh(payload: dict[str, Any], *, buffer_seconds: int = 300) -> bool:
    exp = payload.get("expires_at")
    if exp is None:
        return False
    try:
        return float(exp) <= time.time() + buffer_seconds
    except (TypeError, ValueError):
        return False


async def refresh_oauth_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Return updated payload with fresh access_token (and optional refresh_token rotation)."""
    if provider not in _REFRESHABLE:
        return payload
    rt = str(payload.get("refresh_token") or "").strip()
    if not rt:
        return payload

    if provider == PROVIDER_TWITTER_OAUTH:
        data = await _refresh_twitter(rt)
    elif provider == PROVIDER_LINKEDIN_OAUTH:
        data = await _refresh_linkedin(rt)
    elif provider == PROVIDER_REDDIT_OAUTH:
        data = await reddit_refresh_access_token(rt)
    elif provider == PROVIDER_GOOGLE_YOUTUBE_OAUTH:
        data = await google_refresh_access_token(rt)
    else:
        return payload

    merged = dict(payload)
    at = str(data.get("access_token", ""))
    if at:
        merged["access_token"] = at
    new_rt = data.get("refresh_token")
    if new_rt:
        merged["refresh_token"] = str(new_rt)
    return attach_token_expiry(merged, data)


async def _refresh_twitter(refresh_token: str) -> dict[str, Any]:
    r = await integration_request(
        "POST",
        "https://api.twitter.com/2/oauth2/token",
        provider="twitter_oauth",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        auth=(settings.twitter_client_id or "", settings.twitter_client_secret or ""),
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.twitter_client_id,
        },
    )
    data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(data.get("error_description") or data.get("error") or "twitter_refresh_failed")
    return data


async def _refresh_linkedin(refresh_token: str) -> dict[str, Any]:
    r = await integration_request(
        "POST",
        "https://www.linkedin.com/oauth/v2/accessToken",
        provider="linkedin_oauth",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        },
    )
    data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(data.get("error_description") or data.get("error") or "linkedin_refresh_failed")
    return data
