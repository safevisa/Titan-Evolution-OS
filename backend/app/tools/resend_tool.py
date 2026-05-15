"""Resend email sending — gracefully skips when key not configured."""
from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings

_FROM = "Titan OS <noreply@tokenply.world>"


async def send_email(*, to: str, subject: str, body: str) -> bool:
    """Sends email via Resend. Returns True on success, False otherwise."""
    if not settings.resend_api_key:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={"from": _FROM, "to": [to], "subject": subject, "text": body},
            )
            return resp.status_code == 200
    except Exception:
        return False


async def resend_send_email(**kwargs: Any) -> bool:
    """Adapter for `tool_registry` / integrations."""
    to = kwargs.get("to")
    if not to:
        return False
    subject = str(kwargs.get("subject", ""))
    body = str(kwargs.get("body", ""))
    return await send_email(to=str(to), subject=subject, body=body)
