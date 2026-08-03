"""
/v1/status  — overall Epic Games status
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import (
    compute_health_score,
    make_meta,
    now_iso,
    parse_component,
)
from app.models import (
    MetaBlock,
    OverallIndicator,
    StatusBlock,
    StatusResponse,
    SummaryResponse,
)

router = APIRouter(prefix="/v1/status", tags=["Status"])

_INDICATOR_DESCRIPTION = {
    "none": "All systems operational",
    "minor": "Minor service disruption",
    "major": "Major service disruption",
    "critical": "Critical outage in progress",
}


async def _fetch_status_data() -> Optional[Dict[str, Any]]:
    return await fetch_json(settings.EPIC_STATUS_URL)


@router.get(
    "",
    response_model=StatusResponse,
    summary="Overall Epic Games status",
    description=(
        "Returns the high-level Epic Games service status including an overall health "
        "score (0–100), a boolean `is_healthy`, and a plain-text `summary` string "
        "that is ideal for LLM consumption or quick status checks."
    ),
)
async def get_status(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass cache and fetch live data"),
) -> StatusResponse:
    ttl = settings.CACHE_TTL_STATUS
    cache_key = "status:overall"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_status_data)
    cached = not force_refresh

    fetched_at = now_iso()

    if raw is None:
        return StatusResponse(
            page={"id": "", "name": "Epic Games", "url": "https://status.epicgames.com", "time_zone": "UTC", "updated_at": fetched_at},
            status=StatusBlock(indicator=OverallIndicator.none, description="Unable to reach Epic Games status API"),
            health_score=0,
            is_healthy=False,
            summary="⚠️ Unable to reach Epic Games status API. The upstream service may be temporarily unavailable.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    page_raw = raw.get("page", {})
    status_raw = raw.get("status", {})
    components_raw = raw.get("components", [])

    indicator_str = status_raw.get("indicator", "none").lower()
    try:
        indicator = OverallIndicator(indicator_str)
    except ValueError:
        indicator = OverallIndicator.none

    description = status_raw.get("description") or _INDICATOR_DESCRIPTION.get(indicator_str, "")
    components = [parse_component(c) for c in components_raw]
    health_score = compute_health_score(components)
    is_healthy = indicator == OverallIndicator.none

    if is_healthy:
        summary = f"✅ All Epic Games services are operational. Health score: {health_score}/100."
    elif indicator == OverallIndicator.minor:
        summary = f"⚠️ Minor disruption detected on Epic Games services. Health score: {health_score}/100. {description}"
    else:
        summary = f"🚨 {description} — Epic Games is reporting a {indicator.value} issue. Health score: {health_score}/100."

    # Background task: record to DB
    from app.database import record_status
    import asyncio
    asyncio.ensure_future(record_status(indicator.value, description, health_score))

    return StatusResponse(
        page={
            "id": page_raw.get("id", ""),
            "name": page_raw.get("name", "Epic Games"),
            "url": page_raw.get("url", "https://status.epicgames.com"),
            "time_zone": page_raw.get("time_zone", "UTC"),
            "updated_at": page_raw.get("updated_at", fetched_at),
        },
        status=StatusBlock(indicator=indicator, description=description),
        health_score=health_score,
        is_healthy=is_healthy,
        summary=summary,
        meta=make_meta(cached=cached, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/summary",
    response_model=SummaryResponse,
    summary="Full Epic Games status summary",
    description=(
        "Returns the complete Epic Games status page payload including all components, "
        "current incidents, and scheduled maintenances. Heavier than /v1/status — "
        "use the lightweight endpoint for polling, this one for detailed views."
    ),
)
async def get_summary(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass cache and fetch live data"),
) -> SummaryResponse:
    ttl = settings.CACHE_TTL_STATUS
    cache_key = "status:summary"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_status_data)
    fetched_at = now_iso()

    if raw is None:
        return SummaryResponse(
            page={},
            components=[],
            incidents=[],
            scheduled_maintenances=[],
            status=StatusBlock(indicator=OverallIndicator.none, description="Unavailable"),
            health_score=0,
            summary="Unable to fetch Epic Games status summary.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    status_raw = raw.get("status", {})
    indicator_str = status_raw.get("indicator", "none").lower()
    try:
        indicator = OverallIndicator(indicator_str)
    except ValueError:
        indicator = OverallIndicator.none

    components = [parse_component(c) for c in raw.get("components", [])]
    health_score = compute_health_score(components)

    return SummaryResponse(
        page=raw.get("page", {}),
        components=components,
        incidents=raw.get("incidents", []),
        scheduled_maintenances=raw.get("scheduled_maintenances", []),
        status=StatusBlock(
            indicator=indicator,
            description=status_raw.get("description", ""),
        ),
        health_score=health_score,
        summary=(
            f"Epic Games status: {indicator.value}. "
            f"{len(components)} components tracked. "
            f"Health score: {health_score}/100."
        ),
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/history",
    summary="Status check history (last 48 checks)",
    description="Returns the last 48 status snapshots recorded by this API. Useful for trend analysis.",
)
async def get_status_history(
    limit: int = Query(48, ge=1, le=200, description="Number of history records to return"),
) -> Dict[str, Any]:
    from app.database import get_status_history
    history = await get_status_history(limit=limit)
    return {
        "history": history,
        "count": len(history),
        "description": "Status snapshots recorded by this API (most recent first)",
    }
