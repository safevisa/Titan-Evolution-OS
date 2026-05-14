"""Resend email sending — gracefully skips when key not configured."""
from __future__ import annotations

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
