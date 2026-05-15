"""Validate user-supplied webhook URLs before persisting."""
from __future__ import annotations

from urllib.parse import urlparse

from app.integrations.providers import (
    PROVIDER_DISCORD_WEBHOOK,
    PROVIDER_FEISHU_WEBHOOK,
    PROVIDER_SLACK_INCOMING_WEBHOOK,
    PROVIDER_WECHAT_WORK_WEBHOOK,
)


def assert_https_webhook(url: str) -> str:
    u = url.strip()
    p = urlparse(u)
    if p.scheme != "https":
        raise ValueError("webhook URL must use https")
    if not p.netloc:
        raise ValueError("invalid webhook URL")
    return u


def validate_webhook_for_provider(provider: str, url: str) -> str:
    u = assert_https_webhook(url)
    host = urlparse(u).netloc.lower()

    if provider == PROVIDER_DISCORD_WEBHOOK:
        if "discord.com" not in host and "discordapp.com" not in host:
            raise ValueError("Discord webhook host must be discord.com or discordapp.com")
        if "/api/webhooks/" not in urlparse(u).path:
            raise ValueError("Discord webhook path must contain /api/webhooks/")
        return u

    if provider == PROVIDER_SLACK_INCOMING_WEBHOOK:
        if "hooks.slack.com" not in host:
            raise ValueError("Slack incoming webhook host must be hooks.slack.com")
        return u

    if provider == PROVIDER_FEISHU_WEBHOOK:
        ok = "open.feishu.cn" in host or "larksuite.com" in host or "open.larksuite.com" in host
        if not ok:
            raise ValueError("Feishu/Lark webhook host must be open.feishu.cn or larksuite.com")
        return u

    if provider == PROVIDER_WECHAT_WORK_WEBHOOK:
        if "qyapi.weixin.qq.com" not in host:
            raise ValueError("WeChat Work robot URL host must be qyapi.weixin.qq.com")
        return u

    raise ValueError(f"unknown webhook provider {provider}")
