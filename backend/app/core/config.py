from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/titan"
    sync_database_url: str = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/titan"
    redis_url: str = "redis://127.0.0.1:6379/0"
    qdrant_url: str = "http://127.0.0.1:6333"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    deepseek_api_base: Optional[str] = None
    mistral_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    togetherai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    xai_api_key: Optional[str] = None
    perplexityai_api_key: Optional[str] = None
    exa_api_key: Optional[str] = None
    dashscope_api_key: Optional[str] = None
    moonshot_api_key: Optional[str] = None
    zhipuai_api_key: Optional[str] = None
    baichuan_api_key: Optional[str] = None
    siliconflow_api_key: Optional[str] = None
    minimax_api_key: Optional[str] = None
    minimax_api_base: Optional[str] = None
    volcengine_api_key: Optional[str] = None
    ark_api_key: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_api_base: Optional[str] = None
    azure_api_version: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region_name: Optional[str] = None
    litellm_default_model: str = "deepseek/deepseek-v4-pro"
    apollo_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    db_echo: bool = False
    # Shared secret for POST /api/v1/admin/* (must match frontend server env TITAN_ADMIN_API_KEY).
    titan_admin_api_key: Optional[str] = None
    # Fernet key (urlsafe base64 32-byte) for encrypting integration tokens / webhook URLs at rest.
    titan_integrations_fernet_key: Optional[str] = None
    # Previous Fernet key during rotation — decrypt only; new writes use primary key above.
    titan_integrations_fernet_key_previous: Optional[str] = None
    # Public API base URL (no trailing slash), used for OAuth redirect_uri, e.g. https://api.example.com
    titan_api_public_base_url: Optional[str] = None
    # Slack OAuth (optional; enables "Add to Slack" flow for slack_post_message).
    slack_client_id: Optional[str] = None
    slack_client_secret: Optional[str] = None
    # X (Twitter) OAuth 2.0 — confidential client with PKCE.
    twitter_client_id: Optional[str] = None
    twitter_client_secret: Optional[str] = None
    # LinkedIn OAuth 2.0 (Share on LinkedIn / member posts).
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    # Meta Facebook / Instagram (OAuth for Page + optional IG business account).
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    # Sina Weibo OAuth.
    weibo_app_key: Optional[str] = None
    weibo_app_secret: Optional[str] = None
    # Reddit OAuth (script / web app).
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    # Google OAuth for YouTube Data API (separate from GOOGLE_API_KEY / Gemini).
    google_oauth_client_id: Optional[str] = None
    google_oauth_client_secret: Optional[str] = None
    # TEO-DUAL: Context Sync (Gmail + Calendar) — may reuse google_oauth_* if unset.
    google_workspace_oauth_client_id: Optional[str] = None
    google_workspace_oauth_client_secret: Optional[str] = None
    github_oauth_client_id: Optional[str] = None
    github_oauth_client_secret: Optional[str] = None
    context_sync_interval_sec: int = 1200
    # TEO-DUAL: Computer Use runner (M03).
    computer_use_runner_url: Optional[str] = None
    computer_use_runner_token: Optional[str] = None
    computer_use_ground_url: Optional[str] = None
    computer_use_ground_model: str = "ui-tars-1.5-7b"
    computer_use_max_concurrent: int = 2
    computer_use_artifact_dir: str = "/var/titan/cu-artifacts"
    # TEO-DUAL: OpenHuman sidecar JWT (M04).
    titan_sidecar_jwt_secret: Optional[str] = None
    # MCP stdio servers (optional; complements capability catalog).
    mcp_autostart: bool = True
    brave_api_key: Optional[str] = None
    github_token: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_team_id: Optional[str] = None
    notion_api_key: Optional[str] = None


settings = Settings()
