"""OrbitOps centralized application settings and configuration."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """OrbitOps backend application settings."""

    model_config = SettingsConfigDict(
        env_prefix="ORBITOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "OrbitOps Mission Control API"
    app_version: str = "0.1.0"
    env: str = "development"
    debug: bool = True
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    database_url: str = "sqlite:///./orbitops.sqlite3"
    simulation_mode: bool = True


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


settings = get_settings()
