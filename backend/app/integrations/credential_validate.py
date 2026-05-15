"""Validate non-OAuth integration payloads before encryption."""
from __future__ import annotations

import re
from typing import Any

from app.integrations.providers import (
    PROVIDER_TELEGRAM_BOT,
    PROVIDER_WECHAT_MP_CREDENTIALS,
    PROVIDER_WHATSAPP_CLOUD,
)

_TELEGRAM_TOKEN = re.compile(r"^\d{6,}:[A-Za-z0-9_-]{30,}$")


def validate_credential_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    if provider == PROVIDER_TELEGRAM_BOT:
        token = str(payload.get("bot_token", "")).strip()
        if not _TELEGRAM_TOKEN.match(token):
            raise ValueError("Invalid Telegram bot_token format (expected 123456:ABC... from @BotFather)")
        return {"bot_token": token}

    if provider == PROVIDER_WHATSAPP_CLOUD:
        at = str(payload.get("access_token", "")).strip()
        pn = str(payload.get("phone_number_id", "")).strip()
        if len(at) < 32:
            raise ValueError("WhatsApp access_token looks too short")
        if not pn.isdigit():
            raise ValueError("phone_number_id must be numeric (Meta Cloud API Phone number ID)")
        return {"access_token": at, "phone_number_id": pn}

    if provider == PROVIDER_WECHAT_MP_CREDENTIALS:
        app_id = str(payload.get("app_id", "")).strip()
        secret = str(payload.get("app_secret", "")).strip()
        if len(app_id) < 4 or len(secret) < 4:
            raise ValueError("WeChat Official Account app_id and app_secret are required")
        return {"app_id": app_id, "app_secret": secret}

    raise ValueError(f"Unknown credential provider: {provider}")
