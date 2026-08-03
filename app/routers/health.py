"""
/health — lightweight API health check (no upstream calls)
"""
from __future__ import annotations

import time

from fastapi import APIRouter

from app.cache import cache
from app.config import settings
from app.models import CacheStatsResponse, HealthResponse

router = APIRouter(tags=["API Health"])

_START_TIME = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="API health check",
    description=(
        "Returns API uptime, version, and cache statistics. "
        "Does NOT call any Epic Games APIs — safe to use as a liveness probe. "
        "Returns HTTP 200 when the API is running."
    ),
)
async def health_check() -> HealthResponse:
    stats = cache.stats()
    return HealthResponse(
        status="ok",
        version=settings.API_VERSION,
        uptime_seconds=round(time.monotonic() - _START_TIME, 2),
        cache_stats=CacheStatsResponse(**stats),
    )


@router.get(
    "/ping",
    summary="Minimal ping / liveness probe",
    description="Returns `{\"pong\": true}`. Use as a Kubernetes liveness probe or uptime check.",
)
async def ping() -> dict:
    return {"pong": True}
