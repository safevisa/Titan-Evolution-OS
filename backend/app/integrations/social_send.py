"""HTTP calls to Discord / Slack / Feishu / WeChat / X / LinkedIn after credentials are loaded."""
from __future__ import annotations

import json
from typing import Any

import httpx


async def post_discord_webhook(webhook_url: str, content: str) -> dict[str, Any]:
    text = (content or "")[:2000]
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(webhook_url, json={"content": text})
        ok = r.status_code in (200, 204)
        return {"http_status": r.status_code, "ok": ok, "body_preview": r.text[:500] if r.text else ""}


async def post_slack_incoming_webhook(webhook_url: str, text: str) -> dict[str, Any]:
    payload = {"text": (text or "")[:40000]}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(webhook_url, json=payload)
        body = r.text or ""
        ok = r.status_code == 200 and "ok" in body.lower()
        return {"http_status": r.status_code, "ok": ok, "body_preview": body[:500]}


async def post_feishu_text_webhook(webhook_url: str, text: str) -> dict[str, Any]:
    payload = {"msg_type": "text", "content": {"text": (text or "")[:20000]}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(webhook_url, json=payload)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:500]}
        ok = r.status_code == 200
        if isinstance(data, dict):
            sc = data.get("StatusCode", data.get("code"))
            if sc is not None:
                ok = ok and int(sc) == 0
        return {"http_status": r.status_code, "ok": ok, "response": data}


async def post_wechat_work_markdown(webhook_url: str, markdown: str) -> dict[str, Any]:
    payload = {"msgtype": "markdown", "markdown": {"content": (markdown or "")[:4096]}}
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(webhook_url, json=payload)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:500]}
        ok = r.status_code == 200 and data.get("errcode", 0) == 0
        return {"http_status": r.status_code, "ok": ok, "response": data}


async def post_slack_chat_message(access_token: str, channel: str, text: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json; charset=utf-8"},
            json={"channel": channel, "text": (text or "")[:40000]},
        )
        data = r.json()
        ok = bool(data.get("ok"))
        return {"http_status": r.status_code, "ok": ok, "slack_response": data}


async def post_twitter_create_tweet(access_token: str, text: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20.0) as client:
        r = await client.post(
            "https://api.twitter.com/2/tweets",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"text": (text or "")[:280]},
        )
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:500]}
        ok = r.status_code in (200, 201) and "data" in data
        return {"http_status": r.status_code, "ok": ok, "twitter_response": data}


async def post_linkedin_text_post(access_token: str, author_urn: str, text: str) -> dict[str, Any]:
    body = {
        "author": author_urn,
        "commentary": (text or "")[:3000],
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    headers = {
        "Authorization": f"Bearer {access_token}",
        "LinkedIn-Version": "202405",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        r = await client.post("https://api.linkedin.com/rest/posts", headers=headers, content=json.dumps(body))
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:800]}
        ok = r.status_code in (200, 201)
        return {"http_status": r.status_code, "ok": ok, "linkedin_response": data}
