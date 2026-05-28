"""Core configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Sarvam AI
    sarvam_api_key: str = ""
    sarvam_base_url: str = "https://api.sarvam.ai/v1"
    sarvam_model: str = "sarvam-m"

    # LangSmith
    langsmith_api_key: str = ""
    langchain_tracing_v2: str = "true"
    langchain_project: str = "agitator-rye"

    # Database
    database_url: str = "sqlite:///./agitator_rye.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Security
    secret_key: str = "agitator-rye-dev-secret"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
