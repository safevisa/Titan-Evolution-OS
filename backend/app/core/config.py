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


settings = Settings()
