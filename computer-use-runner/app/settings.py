"""Runner service settings (Agent-S / gui-agents isolated from Titan API)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    runner_token: str = Field(default="dev-runner-token", validation_alias="COMPUTER_USE_RUNNER_TOKEN")
    agent_s_mode: str = Field(default="stub", validation_alias="AGENT_S_MODE")
    platform: str = Field(default="linux", validation_alias="COMPUTER_USE_PLATFORM")
    max_steps_hard: int = Field(default=50, validation_alias="COMPUTER_USE_MAX_STEPS_HARD")
    artifact_dir: str = Field(default="/var/titan/cu-artifacts", validation_alias="COMPUTER_USE_ARTIFACT_DIR")
    enable_local_env: bool = Field(default=False, validation_alias="COMPUTER_USE_ENABLE_LOCAL_ENV")
    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    ground_url: str | None = Field(default=None, validation_alias="COMPUTER_USE_GROUND_URL")
    ground_model: str = Field(default="ui-tars-1.5-7b", validation_alias="COMPUTER_USE_GROUND_MODEL")
    ground_width: int = Field(default=1920, validation_alias="COMPUTER_USE_GROUND_WIDTH")
    ground_height: int = Field(default=1080, validation_alias="COMPUTER_USE_GROUND_HEIGHT")
    xvfb_display: str = Field(default=":99", validation_alias="DISPLAY")
    screen_width: int = Field(default=1920, validation_alias="COMPUTER_USE_SCREEN_WIDTH")
    screen_height: int = Field(default=1080, validation_alias="COMPUTER_USE_SCREEN_HEIGHT")


@lru_cache
def get_settings() -> Settings:
    return Settings()
