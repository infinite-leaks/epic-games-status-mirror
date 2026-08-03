"""
Shared helpers used by multiple routers.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from app.models import (
    Component,
    ComponentStatus,
    Incident,
    IncidentUpdate,
    MetaBlock,
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def next_poll_iso(ttl_seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()


def make_meta(cached: bool, ttl: int, fetched_at: Optional[str] = None) -> MetaBlock:
    return MetaBlock(
        cached=cached,
        cache_ttl_seconds=ttl,
        fetched_at=fetched_at or now_iso(),
        next_poll_at=next_poll_iso(ttl),
    )


def parse_component(raw: Dict[str, Any]) -> Component:
    status_raw = raw.get("status", "unknown").lower()
    try:
        status = ComponentStatus(status_raw)
    except ValueError:
        status = ComponentStatus.unknown
    return Component(
        id=raw.get("id", ""),
        name=raw.get("name", "Unknown"),
        status=status,
        description=raw.get("description"),
        created_at=raw.get("created_at"),
        updated_at=raw.get("updated_at"),
        position=raw.get("position"),
        showcase=raw.get("showcase"),
        start_date=raw.get("start_date"),
        group_id=raw.get("group_id"),
        group=raw.get("group"),
        only_show_if_degraded=raw.get("only_show_if_degraded"),
    )


def parse_incident(raw: Dict[str, Any]) -> Incident:
    from app.models import IncidentImpact, IncidentStatus

    updates_raw = raw.get("incident_updates", [])
    updates = []
    for u in updates_raw:
        try:
            updates.append(IncidentUpdate(
                id=u.get("id", ""),
                status=u.get("status", ""),
                body=u.get("body", ""),
                incident_id=u.get("incident_id", raw.get("id", "")),
                created_at=u.get("created_at", ""),
                updated_at=u.get("updated_at", ""),
                display_at=u.get("display_at"),
                affected_components=u.get("affected_components"),
                deliver_notifications=u.get("deliver_notifications"),
                custom_tweet=u.get("custom_tweet"),
                tweet_id=u.get("tweet_id"),
            ))
        except Exception:
            pass

    impact_raw = raw.get("impact", "none").lower()
    try:
        impact = IncidentImpact(impact_raw)
    except ValueError:
        impact = IncidentImpact.none

    status_raw = raw.get("status", "investigating").lower()
    try:
        status = IncidentStatus(status_raw)
    except ValueError:
        status = IncidentStatus.investigating

    latest_update = updates[0].body if updates else None

    # Calculate duration for resolved incidents
    duration_minutes: Optional[int] = None
    resolved_at = raw.get("resolved_at")
    created_at = raw.get("created_at", "")
    if resolved_at and created_at:
        try:
            start = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            end = datetime.fromisoformat(resolved_at.replace("Z", "+00:00"))
            duration_minutes = int((end - start).total_seconds() / 60)
        except Exception:
            pass

    return Incident(
        id=raw.get("id", ""),
        name=raw.get("name", "Unknown Incident"),
        status=status,
        impact=impact,
        created_at=created_at,
        updated_at=raw.get("updated_at", ""),
        resolved_at=resolved_at,
        shortlink=raw.get("shortlink"),
        page_id=raw.get("page_id"),
        incident_updates=updates,
        components=raw.get("components", []),
        latest_update=latest_update,
        duration_minutes=duration_minutes,
    )


def compute_health_score(components: List[Component]) -> int:
    """
    Returns 0–100. Weights:
    • major_outage        → -20 per component (floor 0)
    • partial_outage      → -10 per component
    • degraded_performance→ -5 per component
    • under_maintenance   → -2 per component
    """
    if not components:
        return 100
    score = 100
    for c in components:
        if c.status == ComponentStatus.major_outage:
            score -= 20
        elif c.status == ComponentStatus.partial_outage:
            score -= 10
        elif c.status == ComponentStatus.degraded_performance:
            score -= 5
        elif c.status == ComponentStatus.under_maintenance:
            score -= 2
    return max(0, score)


# Curated service map: display_name → search keywords
SERVICES: List[tuple] = [
    ("Fortnite", "fortnite", ["fortnite"]),
    ("Epic Games Store", "epic-games-store", ["store", "epic games store"]),
    ("Login / Authentication", "login-auth", ["login", "account", "authentication", "auth"]),
    ("Matchmaking", "matchmaking", ["matchmaking", "game services", "lobby"]),
    ("Friends & Social", "friends-social", ["friends", "social"]),
    ("Cloud Save", "cloud-save", ["cloud save", "save"]),
    ("Launcher / Downloads", "launcher-downloads", ["download", "launcher"]),
    ("Payment Processing", "payments", ["payment", "purchase"]),
    ("Support", "support", ["support", "help"]),
    ("Rocket League", "rocket-league", ["rocket league"]),
    ("Fall Guys", "fall-guys", ["fall guys"]),
    ("Easy Anti-Cheat", "eac", ["anti", "cheat", "eac", "easy anti", "anticheat"]),
]


def find_component_by_keywords(
    components: List[Component], keywords: List[str]
) -> Optional[Component]:
    for comp in components:
        name = comp.name.lower()
        if any(kw.lower() in name for kw in keywords):
            return comp
    return None
