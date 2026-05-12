from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _parse_csv_ints(value: Any) -> list[int]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [int(item) for item in value]
    return [int(item.strip()) for item in str(value).split(",") if item.strip()]


def _parse_csv_strings(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    telegram_bot_token: SecretStr
    openai_api_key: SecretStr
    openai_model: str = "gpt-4.1-mini"

    owner_ids: Annotated[list[int], NoDecode] = Field(min_length=1)
    admin_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)
    viewer_ids: Annotated[list[int], NoDecode] = Field(default_factory=list)

    database_url: str = "sqlite:///data/serverops.db"
    log_level: str = "INFO"
    bot_language: str = "vi"
    serverops_init_only: bool = False
    log_tail_lines: int = Field(default=200, ge=1, le=1000)
    docker_log_tail_lines: int = Field(default=200, ge=1, le=1000)

    allowed_services: Annotated[list[str], NoDecode] = Field(default_factory=list)
    allowed_containers: Annotated[list[str], NoDecode] = Field(default_factory=list)
    allowed_log_files: Annotated[list[str], NoDecode] = Field(default_factory=list)

    @field_validator("owner_ids", "admin_ids", "viewer_ids", mode="before")
    @classmethod
    def parse_id_list(cls, value: Any) -> list[int]:
        return _parse_csv_ints(value)

    @field_validator("allowed_services", "allowed_containers", "allowed_log_files", mode="before")
    @classmethod
    def parse_string_list(cls, value: Any) -> list[str]:
        return _parse_csv_strings(value)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if normalized not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(sorted(allowed))}")
        return normalized

    @field_validator("bot_language")
    @classmethod
    def validate_bot_language(cls, value: str) -> str:
        normalized = value.lower()
        allowed = {"en", "vi"}
        if normalized not in allowed:
            raise ValueError(f"BOT_LANGUAGE must be one of: {', '.join(sorted(allowed))}")
        return normalized


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
