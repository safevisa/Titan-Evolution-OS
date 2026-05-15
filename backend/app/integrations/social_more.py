"""Extra social / messaging HTTP integrations (Telegram, WhatsApp, Meta, Weibo, Reddit, YouTube, WeChat MP)."""
from __future__ import annotations

import json
from typing import Any

import httpx


async def telegram_send_message(bot_token: str, chat_id: str, text: str) -> dict[str, Any]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": (text or "")[:4096]}
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(url, json=payload)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:500]}
        ok = r.status_code == 200 and bool(data.get("ok"))
        return {"http_status": r.status_code, "ok": ok, "telegram": data}


async def whatsapp_send_text_message(
    access_token: str, phone_number_id: str, to_e164: str, text: str
) -> dict[str, Any]:
    to_clean = to_e164.strip().lstrip("+")
    url = f"https://graph.facebook.com/v21.0/{phone_number_id}/messages"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body: dict[str, Any] = {
        "messaging_product": "whatsapp",
        "to": to_clean,
        "type": "text",
        "text": {"preview_url": False, "body": (text or "")[:4096]},
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(url, headers=headers, json=body)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:800]}
        ok = r.status_code == 200 and "messages" in data
        return {"http_status": r.status_code, "ok": ok, "whatsapp": data}


async def facebook_page_feed_post(
    page_access_token: str, page_id: str, message: str, link: str | None = None
) -> dict[str, Any]:
    params: dict[str, str] = {"access_token": page_access_token, "message": (message or "")[:8000]}
    if link:
        params["link"] = str(link)[:2048]
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(f"https://graph.facebook.com/v19.0/{page_id}/feed", params=params)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:800]}
        ok = r.status_code == 200 and ("id" in data or "post_id" in str(data))
        return {"http_status": r.status_code, "ok": ok, "facebook": data}


async def instagram_publish_single_image(
    page_access_token: str, ig_user_id: str, image_url: str, caption: str
) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        r1 = await client.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": (caption or "")[:2200],
                "access_token": page_access_token,
            },
        )
        d1 = r1.json()
        if r1.status_code != 200 or "id" not in d1:
            return {"http_status": r1.status_code, "ok": False, "instagram_step": "create_container", "data": d1}
        cid = d1["id"]
        r2 = await client.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
            data={"creation_id": cid, "access_token": page_access_token},
        )
        d2 = r2.json()
        ok = r2.status_code == 200 and "id" in d2
        return {"http_status": r2.status_code, "ok": ok, "instagram": d2}


async def weibo_post_update(access_token: str, status: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(
            "https://api.weibo.com/2/statuses/update.json",
            params={"access_token": access_token},
            data={"status": (status or "")[:2000]},
        )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:800]}
        ok = r.status_code == 200 and "id" in data
        return {"http_status": r.status_code, "ok": ok, "weibo": data}


async def reddit_submit_post(
    access_token: str,
    subreddit: str,
    title: str,
    kind: str,
    text: str | None = None,
    url: str | None = None,
) -> dict[str, Any]:
    headers = {
        "Authorization": f"bearer {access_token}",
        "User-Agent": "TitanEvolutionOS/1.0 by titan-evolution-os",
    }
    data: dict[str, str] = {
        "sr": subreddit.lstrip("r/"),
        "title": (title or "")[:300],
        "kind": kind if kind in ("self", "link") else "self",
        "api_type": "json",
    }
    if data["kind"] == "self":
        data["text"] = text or ""
    else:
        data["url"] = url or ""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post("https://oauth.reddit.com/api/submit", headers=headers, data=data)
        try:
            body = r.json()
        except Exception:
            body = {"raw": r.text[:1200]}
        ok = r.status_code == 200 and isinstance(body, dict)
        if ok and "json" in body:
            errs = body["json"].get("errors") or []
            ok = len(errs) == 0
        return {"http_status": r.status_code, "ok": ok, "reddit": body}


async def youtube_comment_thread_insert(
    access_token: str, channel_id: str, video_id: str, text: str
) -> dict[str, Any]:
    body = {
        "snippet": {
            "channelId": channel_id,
            "videoId": video_id,
            "topLevelComment": {"snippet": {"textOriginal": (text or "")[:10000]}},
        }
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post(
            "https://www.googleapis.com/youtube/v3/commentThreads?part=snippet",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            content=json.dumps(body),
        )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:800]}
        ok = r.status_code == 200 and "id" in str(data)
        return {"http_status": r.status_code, "ok": ok, "youtube": data}


async def wechat_mp_get_access_token(app_id: str, app_secret: str) -> tuple[str, int]:
    url = (
        "https://api.weixin.qq.com/cgi-bin/token"
        f"?grant_type=client_credential&appid={app_id}&secret={app_secret}"
    )
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.get(url)
        data = r.json()
    if "access_token" not in data:
        raise ValueError(data.get("errmsg", "wechat_mp_token_failed"))
    return str(data["access_token"]), int(data.get("expires_in", 7200))


async def wechat_mp_template_send(
    app_id: str, app_secret: str, touser: str, template_id: str, template_data: dict[str, Any]
) -> dict[str, Any]:
    at, _ = await wechat_mp_get_access_token(app_id, app_secret)
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={at}"
    body = {"touser": touser, "template_id": template_id, "data": template_data}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(url, json=body)
        data_out = r.json()
    ok = r.status_code == 200 and int(data_out.get("errcode", -1)) == 0
    return {"http_status": r.status_code, "ok": ok, "wechat_mp": data_out}
