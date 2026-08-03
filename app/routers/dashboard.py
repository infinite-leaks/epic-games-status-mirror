"""
/v1/dashboard — full aggregated dashboard response (one call, all data)
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import (
    compute_health_score,
    find_component_by_keywords,
    make_meta,
    now_iso,
    parse_component,
    parse_incident,
)
from app.models import (
    ComponentStatus,
    DashboardResponse,
    IncidentStatus,
    OverallIndicator,
    StatusBlock,
)

# EAC keywords
_EAC_KW = ["anti", "cheat", "eac", "easy anti", "anticheat"]

router = APIRouter(prefix="/v1/dashboard", tags=["Dashboard"])


async def _fetch_all() -> Dict[str, Any]:
    """Fetch all upstream data concurrently."""
    summary_task = fetch_json(settings.EPIC_STATUS_URL)
    incidents_task = fetch_json(settings.EPIC_INCIDENTS_URL)
    free_games_task = fetch_json(
        settings.EPIC_FREE_GAMES_URL,
        params={"locale": "en-US", "country": "US"},
    )
    summary, incidents, free_games = await asyncio.gather(
        summary_task, incidents_task, free_games_task
    )
    return {
        "summary": summary,
        "incidents": incidents,
        "free_games": free_games,
    }


@router.get(
    "",
    response_model=DashboardResponse,
    summary="Full Epic Games dashboard (all data in one call)",
    description=(
        "The most comprehensive endpoint — aggregates status, components, incidents, "
        "EAC, and free games into a single response. All upstream calls are made "
        "concurrently so latency is ~max(individual_call) not ~sum. "
        "Use this for dashboards, LLM context injection, or embedding in agents."
    ),
)
async def get_dashboard(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass all caches"),
) -> DashboardResponse:
    ttl = min(settings.CACHE_TTL_STATUS, settings.CACHE_TTL_INCIDENTS)
    cache_key = "dashboard:full"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_all)
    fetched_at = now_iso()

    if raw is None:
        return DashboardResponse(
            status=StatusBlock(indicator=OverallIndicator.none, description="Unavailable"),
            health_score=0,
            is_healthy=False,
            components_summary={},
            active_incidents=[],
            eac_status=ComponentStatus.unknown,
            current_free_games=[],
            upstream_health={},
            summary="⚠️ Unable to fetch data from Epic Games APIs.",
            generated_at=fetched_at,
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    # ── Status ────────────────────────────────────────────────────────────────
    summary_raw = raw.get("summary") or {}
    status_raw = summary_raw.get("status", {})
    indicator_str = status_raw.get("indicator", "none").lower()
    try:
        indicator = OverallIndicator(indicator_str)
    except ValueError:
        indicator = OverallIndicator.none

    components = [parse_component(c) for c in summary_raw.get("components", [])]
    health_score = compute_health_score(components)
    is_healthy = indicator == OverallIndicator.none

    # ── Components summary ────────────────────────────────────────────────────
    operational = [c for c in components if c.status == ComponentStatus.operational]
    degraded = [c for c in components if c.status != ComponentStatus.operational]
    components_summary = {
        "total": len(components),
        "operational": len(operational),
        "degraded": len(degraded),
        "degraded_names": [c.name for c in degraded],
    }

    # ── Incidents ─────────────────────────────────────────────────────────────
    incidents_raw = raw.get("incidents") or {}
    all_incidents = [parse_incident(i) for i in incidents_raw.get("incidents", [])]
    active_incidents = [
        i for i in all_incidents
        if i.status != IncidentStatus.resolved and not i.resolved_at
    ]

    # ── EAC ───────────────────────────────────────────────────────────────────
    eac_comp = find_component_by_keywords(components, _EAC_KW)
    eac_status = eac_comp.status if eac_comp else ComponentStatus.unknown

    # ── Free games ────────────────────────────────────────────────────────────
    from app.routers.free_games import _parse_games
    free_raw = raw.get("free_games") or {}
    current_free, _ = _parse_games(free_raw) if free_raw else ([], [])

    # ── Summary text ─────────────────────────────────────────────────────────
    parts = []
    if is_healthy:
        parts.append(f"✅ All systems operational (health: {health_score}/100).")
    else:
        parts.append(f"⚠️ Epic Games status: {indicator.value} (health: {health_score}/100).")
    if active_incidents:
        parts.append(f"🚨 {len(active_incidents)} active incident(s).")
    if current_free:
        titles = ", ".join(g.title for g in current_free)
        parts.append(f"🎮 Free now: {titles}.")
    summary_text = " ".join(parts)

    return DashboardResponse(
        status=StatusBlock(
            indicator=indicator,
            description=status_raw.get("description", ""),
        ),
        health_score=health_score,
        is_healthy=is_healthy,
        components_summary=components_summary,
        active_incidents=active_incidents,
        eac_status=eac_status,
        current_free_games=current_free,
        upstream_health={
            "note": "Use GET /v1/upstream for detailed per-endpoint probe results"
        },
        summary=summary_text,
        generated_at=fetched_at,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )
