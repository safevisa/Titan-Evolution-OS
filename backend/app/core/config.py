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
    apollo_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None
    db_echo: bool = False


settings = Settings()
