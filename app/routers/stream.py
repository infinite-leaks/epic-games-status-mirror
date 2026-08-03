"""
/v1/stream — Server-Sent Events (SSE) live status stream.

Connect once and receive real-time status updates every N seconds without polling.
Perfect for dashboards, bots, and LLM tool streams.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/v1/stream", tags=["Live Stream (SSE)"])


async def _status_event_generator(
    interval: int, include_free_games: bool
) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted events at *interval* second intervals."""
    from app.client import fetch_json
    from app.config import settings
    from app.helpers import compute_health_score, now_iso, parse_component
    from app.models import OverallIndicator

    tick = 0
    while True:
        try:
            summary_raw = await fetch_json(settings.EPIC_STATUS_URL)
            incidents_raw = await fetch_json(settings.EPIC_INCIDENTS_URL)

            status_indicator = "none"
            health_score = 100
            active_incidents = 0
            free_games_summary = None

            if summary_raw:
                status_indicator = summary_raw.get("status", {}).get("indicator", "none")
                components = [parse_component(c) for c in summary_raw.get("components", [])]
                health_score = compute_health_score(components)

            if incidents_raw:
                all_inc = incidents_raw.get("incidents", [])
                active_incidents = sum(
                    1 for i in all_inc
                    if i.get("status") != "resolved" and not i.get("resolved_at")
                )

            if include_free_games and tick % 10 == 0:  # every 10 ticks
                fg_raw = await fetch_json(
                    settings.EPIC_FREE_GAMES_URL,
                    params={"locale": "en-US"},
                )
                if fg_raw:
                    from app.routers.free_games import _parse_games
                    current, _ = _parse_games(fg_raw)
                    free_games_summary = [g.title for g in current]

            payload = {
                "event": "status_update",
                "timestamp": now_iso(),
                "indicator": status_indicator,
                "health_score": health_score,
                "active_incidents": active_incidents,
                "is_healthy": status_indicator == "none",
            }
            if free_games_summary is not None:
                payload["free_games"] = free_games_summary

            yield f"data: {json.dumps(payload)}\n\n"
            tick += 1
            await asyncio.sleep(interval)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            error_payload = {
                "event": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "message": str(exc),
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
            await asyncio.sleep(interval)


@router.get(
    "",
    summary="Live status stream via Server-Sent Events",
    description=(
        "Opens a persistent SSE connection and pushes Epic Games status updates at "
        "the specified interval (default 30 s, min 10 s, max 300 s). "
        "Each event is a JSON object with `indicator`, `health_score`, `active_incidents`, and `is_healthy`. "
        "Connect with `EventSource` in the browser or `httpx` / `requests` with streaming.\n\n"
        "```js\n"
        "const es = new EventSource('/v1/stream');\n"
        "es.onmessage = e => console.log(JSON.parse(e.data));\n"
        "```"
    ),
    response_class=StreamingResponse,
)
async def live_status_stream(
    interval: int = Query(30, ge=10, le=300, description="Seconds between updates"),
    free_games: bool = Query(False, description="Include free games in the stream (checked every 10 ticks)"),
) -> StreamingResponse:
    return StreamingResponse(
        _status_event_generator(interval, free_games),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
            "Connection": "keep-alive",
        },
    )
