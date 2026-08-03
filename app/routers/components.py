"""
/v1/components — all Epic Games service components with filtering
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import compute_health_score, make_meta, now_iso, parse_component
from app.models import Component, ComponentStatus, ComponentsResponse

router = APIRouter(prefix="/v1/components", tags=["Components"])


async def _fetch_components() -> Optional[Dict[str, Any]]:
    return await fetch_json(settings.EPIC_COMPONENTS_URL)


@router.get(
    "",
    response_model=ComponentsResponse,
    summary="All Epic Games components",
    description=(
        "Lists every component Epic exposes on their status page. "
        "Filter by `status` or `search` to narrow results. "
        "Set `issues_only=true` to see only degraded/outage components."
    ),
)
async def get_components(
    request: Request,
    status: Optional[ComponentStatus] = Query(None, description="Filter by component status"),
    search: Optional[str] = Query(None, description="Search component names (case-insensitive substring)"),
    issues_only: bool = Query(False, description="Return only components with issues"),
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> ComponentsResponse:
    ttl = settings.CACHE_TTL_COMPONENTS
    cache_key = "components:all"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_components)
    fetched_at = now_iso()

    if raw is None:
        return ComponentsResponse(
            page={},
            components=[],
            total=0,
            operational_count=0,
            degraded_count=0,
            summary="Unable to fetch components from Epic Games.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    all_components = [parse_component(c) for c in raw.get("components", [])]

    # Apply filters
    filtered = all_components
    if issues_only:
        filtered = [c for c in filtered if c.status != ComponentStatus.operational]
    if status:
        filtered = [c for c in filtered if c.status == status]
    if search:
        q = search.lower()
        filtered = [c for c in filtered if q in c.name.lower()]

    operational = sum(1 for c in all_components if c.status == ComponentStatus.operational)
    degraded = len(all_components) - operational

    issues_list = [c.name for c in filtered if c.status != ComponentStatus.operational]
    if issues_list:
        summary = (
            f"{degraded} of {len(all_components)} components have issues: "
            + ", ".join(issues_list[:5])
            + ("..." if len(issues_list) > 5 else "")
        )
    else:
        summary = f"All {operational} Epic Games components are operational."

    return ComponentsResponse(
        page=raw.get("page", {}),
        components=filtered,
        total=len(filtered),
        operational_count=operational,
        degraded_count=degraded,
        summary=summary,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/{component_id}",
    summary="Single component by ID",
    description="Returns status and metadata for a specific Epic Games component by its ID.",
)
async def get_component(
    component_id: str,
    request: Request,
) -> Dict[str, Any]:
    ttl = settings.CACHE_TTL_COMPONENTS
    cache_key = "components:all"

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_components)
    fetched_at = now_iso()

    if raw is None:
        return {"error": "Unable to fetch components", "component_id": component_id}

    for c in raw.get("components", []):
        if c.get("id") == component_id:
            component = parse_component(c)
            return {
                "component": component,
                "found": True,
                "meta": make_meta(cached=True, ttl=ttl, fetched_at=fetched_at),
            }

    return {
        "found": False,
        "component_id": component_id,
        "message": "Component not found. Use GET /v1/components to list all available component IDs.",
    }
