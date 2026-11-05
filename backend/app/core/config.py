
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    PROJECT_NAME: str = "GlobalSearch"
    VERSION: str = "0.4.0"
    DESCRIPTION: str = (
        "Worldwide AI-powered Job Discovery and Application Platform"
    )

    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""

    SECRET_KEY: str = "CHANGE_THIS_IN_PRODUCTION"
    AUTH_TIMEOUT_SECONDS: float = 10.0

    REDIS_URL: str = "redis://localhost:6379/0"

    # Only these email addresses can manage shared job sources.
    ADMIN_EMAILS: list[str] = []

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
