"""
Lightweight SQLite persistence via aiosqlite.

Stores:
• status_history  – status snapshots every poll cycle
• incident_history – seen incidents (for trend / diff queries)
• eac_history     – EAC-specific change log

The DB is optional; if it fails to initialise the API keeps running.
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from app.config import settings

logger = logging.getLogger("epicapi.db")

_DB_PATH = Path(settings.DATABASE_PATH)

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS status_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TEXT    NOT NULL,
    indicator   TEXT    NOT NULL,
    description TEXT    NOT NULL,
    health_score INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS incident_history (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    impact      TEXT NOT NULL,
    status      TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    resolved_at TEXT,
    raw_json    TEXT
);

CREATE TABLE IF NOT EXISTS eac_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at TEXT NOT NULL,
    status      TEXT NOT NULL,
    previous    TEXT
);

CREATE INDEX IF NOT EXISTS idx_status_history_recorded_at ON status_history(recorded_at);
CREATE INDEX IF NOT EXISTS idx_incident_history_created_at ON incident_history(created_at);
CREATE INDEX IF NOT EXISTS idx_eac_history_recorded_at ON eac_history(recorded_at);
"""


async def init_db() -> None:
    """Create the data directory and tables if they don't exist."""
    try:
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(_DB_PATH) as db:
            await db.executescript(CREATE_TABLES)
            await db.commit()
        logger.info("Database initialised at %s", _DB_PATH)
    except Exception as exc:
        logger.warning("Database init failed (non-fatal): %s", exc)


@asynccontextmanager
async def get_db():
    """Async context manager for DB connections."""
    try:
        db = await aiosqlite.connect(_DB_PATH)
        db.row_factory = aiosqlite.Row
        try:
            yield db
        finally:
            await db.close()
    except Exception as exc:
        logger.warning("DB connection error (non-fatal): %s", exc)
        yield None  # type: ignore[misc]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def record_status(indicator: str, description: str, health_score: int) -> None:
    try:
        async with get_db() as db:
            if db is None:
                return
            await db.execute(
                "INSERT INTO status_history (recorded_at, indicator, description, health_score) VALUES (?,?,?,?)",
                (_now_iso(), indicator, description, health_score),
            )
            await db.commit()
    except Exception as exc:
        logger.debug("record_status failed: %s", exc)


async def record_incidents(incidents: List[Dict[str, Any]]) -> None:
    try:
        async with get_db() as db:
            if db is None:
                return
            for inc in incidents:
                await db.execute(
                    """INSERT OR REPLACE INTO incident_history
                       (id, name, impact, status, created_at, resolved_at, raw_json)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        inc.get("id", ""),
                        inc.get("name", ""),
                        inc.get("impact", ""),
                        inc.get("status", ""),
                        inc.get("created_at", ""),
                        inc.get("resolved_at"),
                        json.dumps(inc),
                    ),
                )
            await db.commit()
    except Exception as exc:
        logger.debug("record_incidents failed: %s", exc)


async def record_eac_change(new_status: str, previous: Optional[str]) -> None:
    try:
        async with get_db() as db:
            if db is None:
                return
            await db.execute(
                "INSERT INTO eac_history (recorded_at, status, previous) VALUES (?,?,?)",
                (_now_iso(), new_status, previous),
            )
            await db.commit()
    except Exception as exc:
        logger.debug("record_eac_change failed: %s", exc)


async def get_status_history(limit: int = 48) -> List[Dict[str, Any]]:
    try:
        async with get_db() as db:
            if db is None:
                return []
            cursor = await db.execute(
                "SELECT * FROM status_history ORDER BY recorded_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


async def get_eac_history(limit: int = 50) -> List[Dict[str, Any]]:
    try:
        async with get_db() as db:
            if db is None:
                return []
            cursor = await db.execute(
                "SELECT * FROM eac_history ORDER BY recorded_at DESC LIMIT ?",
                (limit,),
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


async def get_incident_history(limit: int = 50, active_only: bool = False) -> List[Dict[str, Any]]:
    try:
        async with get_db() as db:
            if db is None:
                return []
            if active_only:
                cursor = await db.execute(
                    "SELECT * FROM incident_history WHERE resolved_at IS NULL ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM incident_history ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []
