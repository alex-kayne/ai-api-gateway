"""Единая конфигурация приложения из .env и переменных окружения."""

from typing import ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    _instance: ClassVar["Settings | None"] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    redis_url: str = "redis://localhost:6379/0"
    openrouter_api_key: str = ""
    openrouter_url: str = "https://openrouter.ai/api/v1/chat/completions"
    http_timeout_seconds: int = Field(default=60, gt=0)

    @classmethod
    def get(cls) -> "Settings":
        """Вернуть единственный экземпляр настроек на время работы процесса."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
