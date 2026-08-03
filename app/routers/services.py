"""
/v1/services — curated list of key Epic Games services with status
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import (
    SERVICES,
    compute_health_score,
    find_component_by_keywords,
    make_meta,
    now_iso,
    parse_component,
)
from app.models import ComponentStatus, ServiceStatus, ServicesResponse

router = APIRouter(prefix="/v1/services", tags=["Services"])


async def _fetch_summary() -> Any:
    return await fetch_json(settings.EPIC_STATUS_URL)


@router.get(
    "",
    response_model=ServicesResponse,
    summary="Curated Epic Games service statuses",
    description=(
        "Returns a hand-curated list of the most important Epic Games services "
        "(Fortnite, Store, Login, Matchmaking, EAC, Rocket League, etc.) matched "
        "from the live component list. Perfect for dashboards and quick health checks."
    ),
)
async def get_services(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> ServicesResponse:
    ttl = settings.CACHE_TTL_STATUS
    cache_key = "services:curated"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _fetch_summary)
    fetched_at = now_iso()

    if raw is None:
        return ServicesResponse(
            services=[],
            all_operational=False,
            degraded_services=[],
            health_score=0,
            summary="Unable to fetch services from Epic Games.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    all_components = [parse_component(c) for c in raw.get("components", [])]

    service_list = []
    for display_name, slug, keywords in SERVICES:
        comp = find_component_by_keywords(all_components, keywords)
        status = comp.status if comp else ComponentStatus.unknown
        service_list.append(ServiceStatus(
            name=display_name,
            slug=slug,
            status=status,
            component_id=comp.id if comp else None,
            description=comp.description or "" if comp else f"{display_name} component not found",
            is_gaming_service=True,
        ))

    degraded = [s.name for s in service_list if s.status != ComponentStatus.operational and s.status != ComponentStatus.unknown]
    all_op = len(degraded) == 0

    # Build a mini component list for health score
    from app.models import Component
    pseudo_components = [
        Component(id=s.slug, name=s.name, status=s.status)
        for s in service_list
        if s.status != ComponentStatus.unknown
    ]
    health_score = compute_health_score(pseudo_components)

    if all_op:
        summary = f"✅ All {len(service_list)} monitored Epic Games services are operational."
    else:
        summary = (
            f"⚠️ {len(degraded)} service(s) have issues: "
            + ", ".join(degraded)
            + f". Health score: {health_score}/100."
        )

    return ServicesResponse(
        services=service_list,
        all_operational=all_op,
        degraded_services=degraded,
        health_score=health_score,
        summary=summary,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/{slug}",
    summary="Single service by slug",
    description=(
        "Returns status for a single curated service by slug. "
        "Available slugs: fortnite, epic-games-store, login-auth, matchmaking, "
        "friends-social, cloud-save, launcher-downloads, payments, support, "
        "rocket-league, fall-guys, eac"
    ),
)
async def get_service(slug: str, request: Request) -> Dict[str, Any]:
    resp = await get_services(request)
    for svc in resp.services:
        if svc.slug == slug:
            return {
                "service": svc,
                "found": True,
                "meta": resp.meta,
            }
    return {
        "found": False,
        "slug": slug,
        "available_slugs": [s.slug for s in resp.services],
    }
