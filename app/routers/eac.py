"""
/v1/eac — Easy Anti-Cheat dedicated monitoring endpoint
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Request

from app.cache import cache
from app.client import fetch_json
from app.config import settings
from app.helpers import (
    find_component_by_keywords,
    make_meta,
    now_iso,
    parse_component,
    parse_incident,
)
from app.models import (
    Component,
    ComponentStatus,
    EACResponse,
    IncidentStatus,
)

router = APIRouter(prefix="/v1/eac", tags=["Easy Anti-Cheat"])

_EAC_KEYWORDS = ["anti", "cheat", "eac", "easy anti", "anticheat", "easy anticheat"]
_EAC_INCIDENT_KEYWORDS = ["anti", "cheat", "eac", "anticheat"]

# In-process EAC state tracker (persists between requests within one process)
_last_eac_status: Optional[str] = None


async def _fetch_summary() -> Optional[Dict[str, Any]]:
    return await fetch_json(settings.EPIC_STATUS_URL)


async def _fetch_incidents() -> Optional[Dict[str, Any]]:
    return await fetch_json(settings.EPIC_INCIDENTS_URL)


@router.get(
    "",
    response_model=EACResponse,
    summary="Easy Anti-Cheat status",
    description=(
        "Returns the current Easy Anti-Cheat (EAC) component status, any EAC-related "
        "active incidents, and a `status_changed` flag indicating if EAC status "
        "changed since the last API poll — great for alerting workflows and LLM tools."
    ),
)
async def get_eac_status(
    request: Request,
    force_refresh: bool = Query(False, description="Bypass cache"),
) -> EACResponse:
    global _last_eac_status

    ttl = settings.CACHE_TTL_EAC
    summary_key = "status:summary_for_eac"
    incidents_key = "incidents:for_eac"

    if force_refresh:
        cache.invalidate(summary_key)
        cache.invalidate(incidents_key)

    summary_raw, incidents_raw = await cache.get_or_fetch(
        summary_key, ttl, _fetch_summary
    ), await cache.get_or_fetch(incidents_key, ttl, _fetch_incidents)

    fetched_at = now_iso()
    cached = not force_refresh

    # --- Find EAC component ---
    eac_component: Optional[Component] = None
    if summary_raw:
        all_components = [parse_component(c) for c in summary_raw.get("components", [])]
        eac_component = find_component_by_keywords(all_components, _EAC_KEYWORDS)

    eac_status = eac_component.status if eac_component else ComponentStatus.unknown
    found = eac_component is not None

    # --- Detect status change ---
    status_changed = _last_eac_status is not None and _last_eac_status != eac_status.value
    previous_status: Optional[ComponentStatus] = None
    if status_changed and _last_eac_status:
        try:
            previous_status = ComponentStatus(_last_eac_status)
        except ValueError:
            pass
        # Record change to DB
        import asyncio
        from app.database import record_eac_change
        asyncio.ensure_future(record_eac_change(eac_status.value, _last_eac_status))

    _last_eac_status = eac_status.value

    # --- Find EAC-related incidents ---
    related_incidents = []
    if incidents_raw:
        for inc_raw in incidents_raw.get("incidents", []):
            name = inc_raw.get("name", "").lower()
            updates = inc_raw.get("incident_updates", [])
            is_eac = any(kw in name for kw in _EAC_INCIDENT_KEYWORDS)
            if not is_eac:
                for update in updates:
                    body = update.get("body", "").lower()
                    if any(kw in body for kw in _EAC_INCIDENT_KEYWORDS):
                        is_eac = True
                        break
            if is_eac:
                related_incidents.append(parse_incident(inc_raw))

    active_eac_incidents = [
        i for i in related_incidents if i.status != IncidentStatus.resolved
    ]

    # --- Build summary ---
    if not found:
        summary = "ℹ️ EAC component not listed in Epic's current status page. No EAC-specific incidents found."
    elif eac_status == ComponentStatus.operational:
        summary = "✅ Easy Anti-Cheat is fully operational."
        if active_eac_incidents:
            summary += f" Note: {len(active_eac_incidents)} EAC-related incident(s) are active."
    else:
        summary = f"⚠️ EAC status: {eac_status.value.replace('_', ' ').title()}."
        if active_eac_incidents:
            summary += f" {len(active_eac_incidents)} related incident(s) active."
    if status_changed:
        summary += f" 🔔 STATUS CHANGED from {_last_eac_status} → {eac_status.value}"

    return EACResponse(
        component=eac_component,
        found=found,
        status=eac_status,
        related_incidents=related_incidents,
        status_changed=status_changed,
        previous_status=previous_status,
        summary=summary,
        meta=make_meta(cached=cached, ttl=ttl, fetched_at=fetched_at),
    )


@router.get(
    "/history",
    summary="EAC status change history",
    description="Returns EAC status changes recorded by this API (from the local database).",
)
async def get_eac_history(
    limit: int = Query(50, ge=1, le=500),
) -> Dict[str, Any]:
    from app.database import get_eac_history
    history = await get_eac_history(limit=limit)
    return {
        "history": history,
        "count": len(history),
        "description": "EAC status changes recorded by this API (most recent first)",
    }
