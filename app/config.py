"""
Central configuration — driven by environment variables with sane defaults.
All values can be overridden via a .env file or real env vars.
"""

from __future__ import annotations

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Server ──────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = int(os.environ.get("PORT", 8000))
    WORKERS: int = 1  # keep at 1 for in-process cache; use Redis for multi-worker

    # ── API metadata ─────────────────────────────────────────────────────────
    API_TITLE: str = "Epic Games Status API"
    API_DESCRIPTION: str = (
        "A production-grade REST + MCP API for Epic Games service status, "
        "incidents, Easy Anti-Cheat tracking, free games, and more."
    )
    API_VERSION: str = "1.0.0"
    API_CONTACT_NAME: str = "Epic Games Status API"
    API_CONTACT_URL: str = "https://github.com/ynwglobal/epic-games-status-monitor"

    # ── Caching (in-process TTL cache) ───────────────────────────────────────
    CACHE_TTL_STATUS: int = 30        # seconds – overall status (fast-changing)
    CACHE_TTL_COMPONENTS: int = 30    # component list
    CACHE_TTL_INCIDENTS: int = 60     # incidents
    CACHE_TTL_EAC: int = 30           # EAC – sensitive, keep fresh
    CACHE_TTL_FREE_GAMES: int = 300   # free games change once a week
    CACHE_TTL_UPSTREAM: int = 60      # upstream API probe

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_DEFAULT: str = "300/minute"   # per IP
    RATE_LIMIT_DASHBOARD: str = "60/minute"  # dashboard is heavier

    # ── Upstream HTTP client ──────────────────────────────────────────────────
    REQUEST_TIMEOUT: float = 12.0
    USER_AGENT: str = (
        "Mozilla/5.0 (compatible; EpicGamesStatusAPI/1.0; "
        "+https://github.com/ynwglobal/epic-games-status-monitor)"
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = False

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_PATH: str = "data/history.db"

    # ── Epic upstream URLs (override if Epic changes them) ───────────────────
    EPIC_STATUS_URL: str = "https://status.epicgames.com/api/v2/summary.json"
    EPIC_STATUS_CURRENT: str = "https://status.epicgames.com/api/v2/status.json"
    EPIC_INCIDENTS_URL: str = "https://status.epicgames.com/api/v2/incidents.json"
    EPIC_COMPONENTS_URL: str = "https://status.epicgames.com/api/v2/components.json"
    EPIC_FREE_GAMES_URL: str = (
        "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    )


settings = Settings()
