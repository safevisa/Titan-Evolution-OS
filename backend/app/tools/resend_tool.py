"""Resend transactional email — requires RESEND_API_KEY."""

from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

RESEND_BASE = "https://api.resend.com"


async def resend_send_email(
    *,
    from_addr: str,
    to: list[str],
    subject: str,
    html: str,
) -> dict[str, Any]:
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is not configured")
    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Content-Type": "application/json",
    }
    body = {"from": from_addr, "to": to, "subject": subject, "html": html}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{RESEND_BASE}/emails", json=body, headers=headers)
        r.raise_for_status()
        return r.json()
