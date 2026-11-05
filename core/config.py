# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    openai_api_key: str
    anthropic_api_key: str | None = None
    langchain_tracing_v2: bool = False
    langchain_api_key: str | None = None
    model_name: str = "gpt-4o"  # 2026 flagship standard for complex reasoning
    temperature: float = 0.2    # Low temp for architectural precision

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()