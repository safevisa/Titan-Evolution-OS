"""Stable provider ids stored in integration_connections.provider."""
from __future__ import annotations

from typing import Final

# Webhooks
PROVIDER_DISCORD_WEBHOOK: Final = "discord_webhook"
PROVIDER_SLACK_INCOMING_WEBHOOK: Final = "slack_incoming_webhook"
PROVIDER_FEISHU_WEBHOOK: Final = "feishu_webhook"
PROVIDER_WECHAT_WORK_WEBHOOK: Final = "wechat_work_webhook"

# User-pasted / credential vault (no browser OAuth)
PROVIDER_TELEGRAM_BOT: Final = "telegram_bot"
PROVIDER_WHATSAPP_CLOUD: Final = "whatsapp_cloud"
PROVIDER_WECHAT_MP_CREDENTIALS: Final = "wechat_mp_credentials"

# OAuth
PROVIDER_SLACK_OAUTH: Final = "slack_oauth"
PROVIDER_TWITTER_OAUTH: Final = "twitter_oauth"
PROVIDER_LINKEDIN_OAUTH: Final = "linkedin_oauth"
PROVIDER_FACEBOOK_GRAPH_OAUTH: Final = "facebook_graph_oauth"
PROVIDER_WEIBO_OAUTH: Final = "weibo_oauth"
PROVIDER_REDDIT_OAUTH: Final = "reddit_oauth"
PROVIDER_GOOGLE_YOUTUBE_OAUTH: Final = "google_youtube_oauth"
PROVIDER_GOOGLE_WORKSPACE_OAUTH: Final = "google_workspace_oauth"
PROVIDER_GITHUB_OAUTH: Final = "github_oauth"

WEBHOOK_PROVIDERS: frozenset[str] = frozenset(
    {
        PROVIDER_DISCORD_WEBHOOK,
        PROVIDER_SLACK_INCOMING_WEBHOOK,
        PROVIDER_FEISHU_WEBHOOK,
        PROVIDER_WECHAT_WORK_WEBHOOK,
    }
)

CREDENTIAL_PROVIDERS: frozenset[str] = frozenset(
    {
        PROVIDER_TELEGRAM_BOT,
        PROVIDER_WHATSAPP_CLOUD,
        PROVIDER_WECHAT_MP_CREDENTIALS,
    }
)

OAUTH_PROVIDERS: frozenset[str] = frozenset(
    {
        PROVIDER_SLACK_OAUTH,
        PROVIDER_TWITTER_OAUTH,
        PROVIDER_LINKEDIN_OAUTH,
        PROVIDER_FACEBOOK_GRAPH_OAUTH,
        PROVIDER_WEIBO_OAUTH,
        PROVIDER_REDDIT_OAUTH,
        PROVIDER_GOOGLE_YOUTUBE_OAUTH,
        PROVIDER_GOOGLE_WORKSPACE_OAUTH,
        PROVIDER_GITHUB_OAUTH,
    }
)

ALL_MANAGED_PROVIDERS: frozenset[str] = WEBHOOK_PROVIDERS | CREDENTIAL_PROVIDERS | OAUTH_PROVIDERS
