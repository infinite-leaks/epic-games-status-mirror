"""
Pydantic v2 response models.
All public API responses use these models — they appear in the OpenAPI spec
and give LLMs/developers precise type information.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class ComponentStatus(str, Enum):
    operational = "operational"
    degraded_performance = "degraded_performance"
    partial_outage = "partial_outage"
    major_outage = "major_outage"
    under_maintenance = "under_maintenance"
    unknown = "unknown"


class IncidentImpact(str, Enum):
    none = "none"
    minor = "minor"
    major = "major"
    critical = "critical"


class IncidentStatus(str, Enum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"
    postmortem = "postmortem"


class OverallIndicator(str, Enum):
    none = "none"
    minor = "minor"
    major = "major"
    critical = "critical"


# ── Shared ─────────────────────────────────────────────────────────────────────

class MetaBlock(BaseModel):
    """Included in every response — helps clients decide when to re-fetch."""
    cached: bool = Field(description="True if the data was served from the API cache")
    cache_ttl_seconds: int = Field(description="Seconds until cache entry expires")
    fetched_at: str = Field(description="ISO-8601 UTC timestamp of when data was last fetched from Epic")
    next_poll_at: str = Field(description="Suggested ISO-8601 UTC time to poll again")
    api_version: str = Field(default="1.0.0")


class ErrorDetail(BaseModel):
    error: str
    message: str
    status_code: int


# ── Components ─────────────────────────────────────────────────────────────────

class Component(BaseModel):
    id: str
    name: str
    status: ComponentStatus
    description: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    position: Optional[int] = None
    showcase: Optional[bool] = None
    start_date: Optional[str] = None
    group_id: Optional[str] = None
    group: Optional[bool] = None
    only_show_if_degraded: Optional[bool] = None


class ComponentsResponse(BaseModel):
    page: Dict[str, Any]
    components: List[Component]
    total: int
    operational_count: int
    degraded_count: int
    summary: str = Field(description="Plain-text summary, great for LLM consumption")
    meta: MetaBlock


# ── Status ─────────────────────────────────────────────────────────────────────

class PageInfo(BaseModel):
    id: str
    name: str
    url: str
    time_zone: str
    updated_at: str


class StatusBlock(BaseModel):
    indicator: OverallIndicator
    description: str


class StatusResponse(BaseModel):
    page: PageInfo
    status: StatusBlock
    health_score: int = Field(
        ge=0, le=100,
        description="Numeric 0–100 health score derived from component statuses"
    )
    is_healthy: bool
    summary: str
    meta: MetaBlock


class SummaryResponse(BaseModel):
    page: Dict[str, Any]
    components: List[Component]
    incidents: List[Dict[str, Any]]
    scheduled_maintenances: List[Dict[str, Any]]
    status: StatusBlock
    health_score: int
    summary: str
    meta: MetaBlock


# ── Incidents ──────────────────────────────────────────────────────────────────

class IncidentUpdate(BaseModel):
    id: str
    status: str
    body: str
    incident_id: str
    created_at: str
    updated_at: str
    display_at: Optional[str] = None
    affected_components: Optional[List[Dict[str, Any]]] = None
    deliver_notifications: Optional[bool] = None
    custom_tweet: Optional[str] = None
    tweet_id: Optional[str] = None


class Incident(BaseModel):
    id: str
    name: str
    status: IncidentStatus
    impact: IncidentImpact
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    shortlink: Optional[str] = None
    page_id: Optional[str] = None
    incident_updates: List[IncidentUpdate] = []
    components: List[Dict[str, Any]] = []
    latest_update: Optional[str] = Field(
        default=None,
        description="Body of the most recent incident update"
    )
    duration_minutes: Optional[int] = Field(
        default=None,
        description="Duration of the incident in minutes (resolved only)"
    )


class IncidentsResponse(BaseModel):
    incidents: List[Incident]
    total: int
    active_count: int
    resolved_count: int
    summary: str
    meta: MetaBlock


# ── EAC ────────────────────────────────────────────────────────────────────────

class EACResponse(BaseModel):
    component: Optional[Component] = None
    found: bool
    status: ComponentStatus
    related_incidents: List[Incident] = []
    status_changed: bool = Field(
        description="True if EAC status changed since the previous API poll"
    )
    previous_status: Optional[ComponentStatus] = None
    summary: str
    meta: MetaBlock


# ── Free Games ─────────────────────────────────────────────────────────────────

class GameImage(BaseModel):
    url: str
    type: Optional[str] = None
    md5: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class FreeGame(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    url_slug: Optional[str] = None
    store_url: Optional[str] = None
    images: List[GameImage] = []
    original_price: Optional[int] = Field(
        default=None, description="Original price in cents"
    )
    publisher: Optional[str] = None
    developer: Optional[str] = None
    offer_end_date: Optional[str] = None
    offer_start_date: Optional[str] = None
    days_remaining: Optional[int] = None
    hours_remaining: Optional[int] = None
    is_current: bool = True


class FreeGamesResponse(BaseModel):
    current: List[FreeGame]
    upcoming: List[FreeGame]
    current_count: int
    upcoming_count: int
    summary: str
    meta: MetaBlock


# ── Services ───────────────────────────────────────────────────────────────────

class ServiceStatus(BaseModel):
    name: str
    slug: str
    status: ComponentStatus
    component_id: Optional[str] = None
    description: str
    is_gaming_service: bool = True


class ServicesResponse(BaseModel):
    services: List[ServiceStatus]
    all_operational: bool
    degraded_services: List[str]
    health_score: int
    summary: str
    meta: MetaBlock


# ── Dashboard ──────────────────────────────────────────────────────────────────

class DashboardResponse(BaseModel):
    status: StatusBlock
    health_score: int
    is_healthy: bool
    components_summary: Dict[str, Any]
    active_incidents: List[Incident]
    eac_status: ComponentStatus
    current_free_games: List[FreeGame]
    upstream_health: Dict[str, Any]
    summary: str
    generated_at: str
    meta: MetaBlock


# ── Upstream / API health ──────────────────────────────────────────────────────

class EndpointProbe(BaseModel):
    name: str
    url: str
    reachable: bool
    status_code: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None


class UpstreamHealthResponse(BaseModel):
    endpoints: List[EndpointProbe]
    operational_count: int
    total: int
    all_operational: bool
    summary: str
    meta: MetaBlock


# ── Cache stats ────────────────────────────────────────────────────────────────

class CacheStatsResponse(BaseModel):
    cached_keys: int
    total_keys_ever: int
    per_key: Dict[str, Any]


# ── Health ─────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    cache_stats: CacheStatsResponse
