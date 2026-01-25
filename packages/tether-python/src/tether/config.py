"""
Configuration management for Tether applications.
"""

from functools import lru_cache
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = SettingsConfigDict(
        env_prefix="TETHER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = False

    # LLM settings
    llm_backend: Literal["local", "openai", "mock"] = "local"
    model_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"

    # Model parameters
    context_length: int = 4096
    default_temperature: float = 0.7
    default_max_tokens: int = 1024

    # CORS settings
    cors_origins: list[str] = ["*"]

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings.
    """
    return Settings()


def reset_settings() -> None:
    """
    Reset settings cache. Useful for testing.
    """
    get_settings.cache_clear()
