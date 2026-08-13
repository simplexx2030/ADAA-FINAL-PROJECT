"""
Application settings for ADAA.

Everything configurable lives here, in one place. Values are read from the
".env" file at the project root. Nothing in the codebase should hard-code an
API key, a model name, or a database URL -- it should ask for it here instead.

Why this matters: the build spec (section 7) requires that the Gemini model
name be changeable through an environment variable, so we can switch models
later without touching any code.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# This file lives at:  <project root>/backend/app/config.py
# So the project root is three levels up from this file.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All ADAA settings, loaded from the .env file."""

    # --- Gemini: the LLM that powers the ADAA agent ---
    # Empty by default so the app can still start (and /health can respond)
    # before you have added a key. The Gemini check script will tell you
    # clearly if the key is missing.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-pro-preview"

    # --- Database ---
    # Not used yet. We start with CSV files (STEP 1) and move to PostgreSQL
    # at STEP 2.
    database_url: str = ""

    # --- Application ---
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # Ignore any extra variables in .env that we do not know about yet,
        # instead of crashing.
        extra="ignore",
    )


# One shared settings object for the whole application.
settings = Settings()
