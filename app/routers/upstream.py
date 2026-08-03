"""
/v1/upstream — probe all upstream Epic Games API endpoints
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import probe_url
from app.config import settings
from app.helpers import make_meta, now_iso
from app.models import EndpointProbe, UpstreamHealthResponse

router = APIRouter(prefix="/v1/upstream", tags=["Upstream Health"])

_ENDPOINTS = [
    ("Epic Status Summary", settings.EPIC_STATUS_URL),
    ("Epic Status Current", settings.EPIC_STATUS_CURRENT),
    ("Epic Incidents", settings.EPIC_INCIDENTS_URL),
    ("Epic Components", settings.EPIC_COMPONENTS_URL),
    ("Epic Free Games Store", settings.EPIC_FREE_GAMES_URL),
]


async def _probe_all() -> Dict[str, Any]:
    results = await asyncio.gather(*[probe_url(url) for _, url in _ENDPOINTS])
    probes = []
    for (name, url), result in zip(_ENDPOINTS, results):
        probes.append({
            "name": name,
            "url": url,
            **result,
        })
    return {"probes": probes}


@router.get(
    "",
    response_model=UpstreamHealthResponse,
    summary="Upstream Epic Games API health",
    description=(
        "Probes all Epic Games upstream API endpoints with HEAD requests and returns "
        "reachability, HTTP status code, and latency in ms for each. Useful for "
        "diagnosing whether failures are on Epic's side or this API's side."
    ),
)
async def get_upstream_health(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> UpstreamHealthResponse:
    ttl = settings.CACHE_TTL_UPSTREAM
    cache_key = "upstream:health"

    if force_refresh:
        cache.invalidate(cache_key)

    raw = await cache.get_or_fetch(cache_key, ttl, _probe_all)
    fetched_at = now_iso()

    if raw is None:
        return UpstreamHealthResponse(
            endpoints=[],
            operational_count=0,
            total=0,
            all_operational=False,
            summary="Unable to probe upstream endpoints.",
            meta=make_meta(cached=False, ttl=ttl, fetched_at=fetched_at),
        )

    probes_raw = raw.get("probes", [])
    probes = [EndpointProbe(**p) for p in probes_raw]
    operational = sum(1 for p in probes if p.reachable)
    total = len(probes)
    all_op = operational == total

    summary = f"{operational}/{total} Epic Games upstream API endpoints are reachable."
    if not all_op:
        failed = [p.name for p in probes if not p.reachable]
        summary += f" Unreachable: {', '.join(failed)}."

    return UpstreamHealthResponse(
        endpoints=probes,
        operational_count=operational,
        total=total,
        all_operational=all_op,
        summary=summary,
        meta=make_meta(cached=not force_refresh, ttl=ttl, fetched_at=fetched_at),
    )
