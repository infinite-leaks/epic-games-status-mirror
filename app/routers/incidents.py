"""
/v1/incidents — active and resolved Epic Games incidents
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import make_meta, now_iso, parse_incident
from app.models import Incident, IncidentImpact, IncidentStatus, IncidentsResponse

router = APIRouter(prefix="/v1/incidents", tags=["Incidents"])


async def _fetch_incidents() -> Optional[Dict[str, Any]]:
    return await fetch_json(settings.EPIC_INCIDENTS_URL)


@router.get(
    "",
    response_model=IncidentsResponse,
    summary="Active and resolved incidents",
    description=(
        "Returns Epic Games incidents. By default returns all (active + resolved). "
        "Use `active_only=true` for incidents currently in progress. "
        "Filter by `impact` (none/minor/major/critical) or `status`."
    ),
)
async def get_incidents(
    request: Request,
    active_only: bool = Query(False, description="Return only unresolved incidents"),
    impact: Optional[IncidentImpact] = Query(None, description="Filter by impact level"),
    limit: int = Query(20, ge=1, le=100, description="Max incidents to return"),
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> IncidentsResponse:
    ttl = settings.CACHE_TTL_INCIDENTS
    cache_key = "incidents:all"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_incidents)
    fetched_at = now_iso()

    if raw is None:
        return IncidentsResponse(
            incidents=[],
            total=0,
            active_count=0,
            resolved_count=0,
            summary="Unable to fetch incidents from Epic Games.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    raw_incidents = raw.get("incidents", [])
    all_incidents = [parse_incident(i) for i in raw_incidents]

    # Record to history DB
    import asyncio
    from app.database import record_incidents
    asyncio.ensure_future(record_incidents(raw_incidents))

    active = [i for i in all_incidents if i.status != IncidentStatus.resolved and not i.resolved_at]
    resolved = [i for i in all_incidents if i.status == IncidentStatus.resolved or i.resolved_at]

    filtered = active if active_only else all_incidents
    if impact:
        filtered = [i for i in filtered if i.impact == impact]
    filtered = filtered[:limit]

    if active:
        names = [i.name for i in active[:3]]
        summary = (
            f"🚨 {len(active)} active incident(s): " + ", ".join(names)
            + ("..." if len(active) > 3 else "")
        )
    else:
        summary = "✅ No active incidents. Epic Games services are running normally."

    return IncidentsResponse(
        incidents=filtered,
        total=len(filtered),
        active_count=len(active),
        resolved_count=len(resolved),
        summary=summary,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/active",
    response_model=IncidentsResponse,
    summary="Active incidents only",
    description="Shortcut for GET /v1/incidents?active_only=true",
)
async def get_active_incidents(
    request: Request,
    impact: Optional[IncidentImpact] = Query(None),
    limit: int = Query(20, ge=1, le=100),
) -> IncidentsResponse:
    return await get_incidents(request, active_only=True, impact=impact, limit=limit, force_refresh=False)


@router.get(
    "/history",
    summary="Incident history (from local DB)",
    description=(
        "Returns incidents stored in this API's local SQLite history database. "
        "This persists across caches and gives you a longer-term view."
    ),
)
async def get_incident_history(
    limit: int = Query(50, ge=1, le=500),
    active_only: bool = Query(False),
) -> Dict[str, Any]:
    from app.database import get_incident_history
    history = await get_incident_history(limit=limit, active_only=active_only)
    return {
        "incidents": history,
        "count": len(history),
        "source": "local_db",
        "description": "Incidents stored in this API's local history database",
    }


@router.get(
    "/{incident_id}",
    response_model=Incident,
    summary="Single incident by ID",
    description="Returns full details of a specific incident including all update timeline entries.",
)
async def get_incident(incident_id: str, request: Request) -> Any:
    ttl = settings.CACHE_TTL_INCIDENTS
    cache_key = "incidents:all"
    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_incidents)

    if raw is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Unable to reach Epic Games incidents API")

    for inc in raw.get("incidents", []):
        if inc.get("id") == incident_id:
            return parse_incident(inc)

    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
