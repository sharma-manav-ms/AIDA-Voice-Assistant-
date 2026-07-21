"""
config.py
---------
Loads environment variables and exposes application configuration.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# ── locate .env at project root ──────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_PATH = _PROJECT_ROOT / ".env"
load_dotenv(_ENV_PATH)


# ── API Keys ─────────────────────────────────────────────────────

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ── Email credentials ────────────────────────────────────────────

EMAIL_ADDRESS: str = os.getenv("EMAIL", "")
EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

# ── Optional service keys ────────────────────────────────────────

WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")
NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")


# ── Paths ────────────────────────────────────────────────────────

PROJECT_ROOT: Path = _PROJECT_ROOT
MEMORY_DIR: Path = _PROJECT_ROOT / "app" / "memory"
LOGS_DIR: Path = MEMORY_DIR / "logs"
NOTES_DIR: Path = MEMORY_DIR / "notes"
TEMP_DIR: Path = MEMORY_DIR / "temp"
DB_PATH: Path = MEMORY_DIR / "history.db"
SCREENSHOTS_DIR: Path = _PROJECT_ROOT / "assets" / "screenshots"

# ensure directories exist
for _dir in (LOGS_DIR, NOTES_DIR, TEMP_DIR, SCREENSHOTS_DIR):
    _dir.mkdir(parents=True, exist_ok=True)


def get_llm_provider() -> str:
    """
    Determine the preferred LLM provider.

    Returns 'gemini' if a Gemini key is set, otherwise 'openai'.
    Raises RuntimeError if neither key is configured.
    """

    if GEMINI_API_KEY:
        return "gemini"

    if OPENAI_API_KEY:
        return "openai"

    raise RuntimeError(
        "No LLM API key found. "
        "Set GEMINI_API_KEY or OPENAI_API_KEY in your .env file."
    )


def validate_email_credentials() -> bool:
    """Return True if email address and password are both set."""

    return bool(EMAIL_ADDRESS) and bool(EMAIL_PASSWORD)
