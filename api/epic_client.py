"""Thin HTTP client around the public Epic Games status + store endpoints.

All functions return plain JSON-serialisable dicts so they can be handed
straight back to FastAPI (and therefore documented by OpenAPI).
"""

from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Optional

import requests

STATUS_SUMMARY_URL = "https://status.epicgames.com/api/v2/summary.json"
STATUS_CURRENT_URL = "https://status.epicgames.com/api/v2/status.json"
INCIDENTS_URL = "https://status.epicgames.com/api/v2/incidents.json"
COMPONENTS_URL = "https://status.epicgames.com/api/v2/components.json"
FREE_GAMES_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"

USER_AGENT = "epic-games-status-mirror/1.0 (+https://github.com/infinite-leaks)"
DEFAULT_TIMEOUT = 15


class UpstreamError(RuntimeError):
    """Raised when an Epic endpoint is unreachable or returns bad data."""


def _get(url: str, *, params: Optional[Dict[str, Any]] = None,
         timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise UpstreamError(f"Request to {url} failed: {exc}") from exc
    except ValueError as exc:
        raise UpstreamError(f"Invalid JSON from {url}: {exc}") from exc


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def get_status() -> Dict[str, Any]:
    """Overall Epic Games platform status indicator + description."""
    data = _get(STATUS_CURRENT_URL)
    status = data.get("status", {})
    return {
        "indicator": status.get("indicator", "unknown"),
        "description": status.get("description", "Unknown"),
        "page": data.get("page", {}),
        "fetched_at": utc_now(),
    }


def get_components() -> Dict[str, Any]:
    """Every component (service) Epic publishes."""
    data = _get(COMPONENTS_URL)
    components = [
        {
            "id": c.get("id"),
            "name": c.get("name"),
            "status": c.get("status"),
            "description": c.get("description"),
            "group": bool(c.get("group")),
            "updated_at": c.get("updated_at"),
        }
        for c in data.get("components", [])
    ]
    return {"count": len(components), "components": components, "fetched_at": utc_now()}


def _match(components: List[Dict[str, Any]], keywords: List[str]) -> List[Dict[str, Any]]:
    lowered = [k.lower() for k in keywords]
    return [c for c in components if any(k in (c.get("name") or "").lower() for k in lowered)]


def get_easy_anticheat() -> Dict[str, Any]:
    """Easy Anti-Cheat related components only."""
    components = get_components()["components"]
    matches = _match(components, ["anti-cheat", "anticheat", "eac", "easy anti"])
    operational = all(c.get("status") == "operational" for c in matches) if matches else None
    return {
        "count": len(matches),
        "all_operational": operational,
        "components": matches,
        "fetched_at": utc_now(),
    }


def get_incidents(limit: int = 10, unresolved_only: bool = False) -> Dict[str, Any]:
    """Recent incident reports, newest first."""
    data = _get(INCIDENTS_URL)
    incidents = data.get("incidents", [])
    if unresolved_only:
        incidents = [i for i in incidents if i.get("status") != "resolved"]
    incidents = incidents[: max(1, min(limit, 100))]
    trimmed = [
        {
            "id": i.get("id"),
            "name": i.get("name"),
            "status": i.get("status"),
            "impact": i.get("impact"),
            "shortlink": i.get("shortlink"),
            "created_at": i.get("created_at"),
            "updated_at": i.get("updated_at"),
            "resolved_at": i.get("resolved_at"),
            "updates": [
                {
                    "status": u.get("status"),
                    "body": u.get("body"),
                    "created_at": u.get("created_at"),
                }
                for u in (i.get("incident_updates") or [])[:5]
            ],
        }
        for i in incidents
    ]
    return {"count": len(trimmed), "incidents": trimmed, "fetched_at": utc_now()}


def get_free_games(country: str = "US", locale: str = "en-US") -> Dict[str, Any]:
    """Current + upcoming Epic Games Store free promotions."""
    data = _get(FREE_GAMES_URL, params={"locale": locale, "country": country,
                                        "allowCountries": country})
    elements = (
        data.get("data", {}).get("Catalog", {}).get("searchStore", {}).get("elements", [])
    )
    current: List[Dict[str, Any]] = []
    upcoming: List[Dict[str, Any]] = []
    for game in elements:
        promotions = game.get("promotions") or {}
        offers_now = promotions.get("promotionalOffers") or []
        offers_next = promotions.get("upcomingPromotionalOffers") or []
        entry = {
            "title": game.get("title"),
            "description": game.get("description"),
            "seller": (game.get("seller") or {}).get("name"),
            "original_price": (
                (game.get("price") or {}).get("totalPrice", {}).get("fmtPrice", {}).get("originalPrice")
            ),
            "url_slug": game.get("productSlug") or game.get("urlSlug"),
        }
        if offers_now:
            window = (offers_now[0].get("promotionalOffers") or [{}])[0]
            entry["starts_at"] = window.get("startDate")
            entry["ends_at"] = window.get("endDate")
            current.append(entry)
        elif offers_next:
            window = (offers_next[0].get("promotionalOffers") or [{}])[0]
            entry["starts_at"] = window.get("startDate")
            entry["ends_at"] = window.get("endDate")
            upcoming.append(entry)
    return {
        "country": country,
        "locale": locale,
        "current": current,
        "upcoming": upcoming,
        "fetched_at": utc_now(),
    }


def get_summary() -> Dict[str, Any]:
    """Everything in one call: status, components, incidents, maintenances."""
    summary = _get(STATUS_SUMMARY_URL)
    return {
        "status": summary.get("status", {}),
        "components": [
            {"id": c.get("id"), "name": c.get("name"), "status": c.get("status")}
            for c in summary.get("components", [])
        ],
        "incidents": [
            {
                "id": i.get("id"),
                "name": i.get("name"),
                "status": i.get("status"),
                "impact": i.get("impact"),
                "updated_at": i.get("updated_at"),
            }
            for i in summary.get("incidents", [])
        ],
        "scheduled_maintenances": summary.get("scheduled_maintenances", []),
        "fetched_at": utc_now(),
    }
