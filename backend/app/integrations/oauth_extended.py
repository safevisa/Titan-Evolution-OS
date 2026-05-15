"""OAuth helpers for Meta (Facebook/Instagram), Weibo, Reddit, Google YouTube."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import settings
from app.integrations.oauth_flows import pack_oauth_state, public_api_base

FACEBOOK_SCOPES = "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish,business_management"
GOOGLE_YOUTUBE_SCOPES = "https://www.googleapis.com/auth/youtube.force-ssl"
REDDIT_SCOPES = "submit,identity,read"


def facebook_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/facebook/callback"


def weibo_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/weibo/callback"


def reddit_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/reddit/callback"


def google_youtube_oauth_redirect_uri() -> str:
    return f"{public_api_base()}/api/v1/integrations/oauth/google-youtube/callback"


def facebook_authorize_url(*, tenant_id: str) -> str:
    if not settings.facebook_app_id or not settings.facebook_app_secret:
        raise ValueError("Facebook/Meta requires FACEBOOK_APP_ID and FACEBOOK_APP_SECRET")
    st = pack_oauth_state(tenant_id, "facebook")
    q = urlencode(
        {
            "client_id": settings.facebook_app_id,
            "redirect_uri": facebook_oauth_redirect_uri(),
            "state": st,
            "response_type": "code",
            "scope": FACEBOOK_SCOPES,
        }
    )
    return f"https://www.facebook.com/v19.0/dialog/oauth?{q}"


async def facebook_exchange_code_for_user_token(code: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": settings.facebook_app_id,
                "client_secret": settings.facebook_app_secret,
                "redirect_uri": facebook_oauth_redirect_uri(),
                "code": code,
            },
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else "facebook_token_failed")
    return str(data["access_token"])


async def facebook_long_lived_user_token(short_token: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": settings.facebook_app_id,
                "client_secret": settings.facebook_app_secret,
                "fb_exchange_token": short_token,
            },
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError("facebook_long_lived_token_failed")
    return str(data["access_token"])


async def facebook_pick_page_and_ig(user_long_token: str) -> tuple[str, str, str | None]:
    """Return (page_access_token, page_id, instagram_user_id_or_none)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(
            "https://graph.facebook.com/v19.0/me/accounts",
            params={
                "fields": "name,access_token,id,instagram_business_account",
                "access_token": user_long_token,
            },
        )
        data = r.json()
    if r.status_code != 200 or "data" not in data or not data["data"]:
        raise ValueError("facebook_no_managed_pages")
    pages: list[dict[str, Any]] = data["data"]

    def ig_id(p: dict[str, Any]) -> str | None:
        ig = p.get("instagram_business_account") or {}
        if isinstance(ig, dict) and ig.get("id"):
            return str(ig["id"])
        return None

    first = next((p for p in pages if ig_id(p)), pages[0])
    page_token = str(first.get("access_token", ""))
    page_id = str(first.get("id", ""))
    ig_id_val = ig_id(first)
    if not page_token or not page_id:
        raise ValueError("facebook_page_token_missing")
    return page_token, page_id, ig_id_val


def weibo_authorize_url(*, tenant_id: str) -> str:
    if not settings.weibo_app_key:
        raise ValueError("Weibo requires WEIBO_APP_KEY (and secret for token exchange)")
    st = pack_oauth_state(tenant_id, "weibo")
    q = urlencode(
        {
            "client_id": settings.weibo_app_key,
            "redirect_uri": weibo_oauth_redirect_uri(),
            "response_type": "code",
            "state": st,
        }
    )
    return f"https://api.weibo.com/oauth2/authorize?{q}"


async def weibo_exchange_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://api.weibo.com/oauth2/access_token",
            data={
                "client_id": settings.weibo_app_key,
                "client_secret": settings.weibo_app_secret or "",
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": weibo_oauth_redirect_uri(),
            },
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "weibo_token_failed"))))
    return data


def reddit_authorize_url(*, tenant_id: str) -> str:
    if not settings.reddit_client_id:
        raise ValueError("Reddit requires REDDIT_CLIENT_ID")
    st = pack_oauth_state(tenant_id, "reddit")
    q = urlencode(
        {
            "client_id": settings.reddit_client_id,
            "response_type": "code",
            "state": st,
            "redirect_uri": reddit_oauth_redirect_uri(),
            "duration": "permanent",
            "scope": REDDIT_SCOPES,
        }
    )
    return f"https://www.reddit.com/api/v1/authorize?{q}"


async def reddit_exchange_code(code: str) -> dict[str, Any]:
    auth = (settings.reddit_client_id or "", settings.reddit_client_secret or "")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=auth,
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": reddit_oauth_redirect_uri()},
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error", "reddit_token_failed")))
    return data


def google_youtube_authorize_url(*, tenant_id: str) -> str:
    if not settings.google_oauth_client_id or not settings.google_oauth_client_secret:
        raise ValueError("YouTube OAuth requires GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET")
    st = pack_oauth_state(tenant_id, "google_youtube")
    q = urlencode(
        {
            "client_id": settings.google_oauth_client_id,
            "redirect_uri": google_youtube_oauth_redirect_uri(),
            "response_type": "code",
            "scope": GOOGLE_YOUTUBE_SCOPES,
            "access_type": "offline",
            "prompt": "consent",
            "state": st,
        }
    )
    return f"https://accounts.google.com/o/oauth2/v2/auth?{q}"


async def google_exchange_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": google_youtube_oauth_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "google_token_failed"))))
    return data


async def reddit_refresh_access_token(refresh_token: str) -> dict[str, Any]:
    auth = (settings.reddit_client_id or "", settings.reddit_client_secret or "")
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            auth=auth,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error", "reddit_refresh_failed")))
    return data


async def google_refresh_access_token(refresh_token: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )
        data = r.json()
    if r.status_code != 200 or "access_token" not in data:
        raise ValueError(str(data.get("error_description", data.get("error", "google_refresh_failed"))))
    return data


async def google_youtube_fetch_channel_id(access_token: str) -> str:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "id", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = r.json()
    if r.status_code != 200:
        raise ValueError(str(data.get("error", {}).get("message", "youtube_channel_list_failed")))
    items = data.get("items") or []
    if not items or "id" not in items[0]:
        raise ValueError("youtube_no_channel_for_account")
    return str(items[0]["id"])
