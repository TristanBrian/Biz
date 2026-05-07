# ============================================================
# app/core/config.py
# Centralised configuration using pydantic-settings.
# All environment variables are validated and typed here.
# Access config anywhere via: from app.core.config import settings
# ============================================================

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    pydantic-settings automatically reads from environment variables
    and validates types — no more raw os.environ calls scattered around.
    """

    # --- Application ---
    APP_NAME: str = "BizSafi API"
    APP_ENV: str = "development"

    # --- Database ---
    DATABASE_URL: str  # Required — must be set in .env

    # --- JWT Authentication ---
    SECRET_KEY: str                         # Required — must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Africa's Talking (SMS) ---
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = "your_at_api_key"

    # --- Anthropic Claude AI ---
    ANTHROPIC_API_KEY: str = "your_anthropic_api_key"

    # Tell pydantic-settings to read from a .env file in the project root
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Singleton — import this instance everywhere
settings = Settings()
