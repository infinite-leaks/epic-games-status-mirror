"""
MCP (Model Context Protocol) server for Epic Games Status API.

Exposes all major API capabilities as MCP tools so LLMs and AI agents can
call them natively via the MCP protocol over HTTP/SSE transport.

Endpoint layout:
  GET  /mcp        — SSE stream (MCP client connects here)
  POST /mcp/messages — MCP client sends messages here

Usage with Claude Desktop (add to claude_desktop_config.json):
  {
    "mcpServers": {
      "epic-games-status": {
        "url": "http://localhost:8000/mcp"
      }
    }
  }
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

logger = logging.getLogger("epicapi.mcp")

# ── Tool registry ─────────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_epic_status",
        "description": (
            "Get the current overall Epic Games service status. "
            "Returns health score (0-100), indicator (none/minor/major/critical), "
            "and a plain-text summary. Use this first for a quick health check."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "force_refresh": {
                    "type": "boolean",
                    "description": "Bypass cache and fetch live data from Epic",
                    "default": False,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_epic_dashboard",
        "description": (
            "Get a full Epic Games dashboard: status, all component health, "
            "active incidents, EAC status, and current free games — all in one call. "
            "Best for getting complete context about Epic Games' current state."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "force_refresh": {
                    "type": "boolean",
                    "description": "Bypass cache and fetch live data",
                    "default": False,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_active_incidents",
        "description": (
            "Get all currently active Epic Games incidents. "
            "Returns incident name, impact (none/minor/major/critical), status, "
            "start time, and the latest update text. "
            "Returns an empty list if there are no active incidents."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "impact": {
                    "type": "string",
                    "enum": ["none", "minor", "major", "critical"],
                    "description": "Filter by impact level",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of incidents to return (1-100)",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_eac_status",
        "description": (
            "Get the current Easy Anti-Cheat (EAC) status and any EAC-related incidents. "
            "Includes `status_changed` flag indicating if EAC status changed since last poll. "
            "Useful for game developers and anti-cheat monitoring workflows."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_free_games",
        "description": (
            "Get the current Epic Games Store free games and upcoming free games. "
            "Returns game title, description, store URL, cover images, publisher, "
            "and countdown (days/hours remaining). Free games rotate weekly."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "locale": {
                    "type": "string",
                    "description": "Locale for game titles (e.g. en-US, de-DE, fr-FR, ja-JP)",
                    "default": "en-US",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_components",
        "description": (
            "Get the status of all Epic Games service components. "
            "Each component has an ID, name, and status (operational/degraded_performance/"
            "partial_outage/major_outage/under_maintenance). "
            "Use `issues_only=true` to see only degraded components."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "issues_only": {
                    "type": "boolean",
                    "description": "Return only components with issues",
                    "default": False,
                },
                "search": {
                    "type": "string",
                    "description": "Search component names (case-insensitive)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_services",
        "description": (
            "Get the status of key Epic Games services: Fortnite, Epic Games Store, "
            "Login/Authentication, Matchmaking, Friends & Social, Cloud Save, "
            "Launcher/Downloads, Payments, Support, Rocket League, Fall Guys, EAC. "
            "Returns a health score and list of any degraded services."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "check_upstream_health",
        "description": (
            "Probe all Epic Games upstream API endpoints and return their reachability, "
            "HTTP status code, and latency in milliseconds. "
            "Use this to diagnose whether a problem is with Epic's APIs or this API."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_status_history",
        "description": (
            "Get historical Epic Games status snapshots stored by this API. "
            "Returns up to 48 records showing the status indicator and health score "
            "over time. Useful for trend analysis and reporting."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of records (1-200)",
                    "default": 24,
                    "minimum": 1,
                    "maximum": 200,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_eac_history",
        "description": (
            "Get EAC (Easy Anti-Cheat) status change history stored by this API. "
            "Shows when EAC status changed and what it changed from/to. "
            "Useful for identifying EAC outage patterns."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of records (1-500)",
                    "default": 20,
                }
            },
            "required": [],
        },
    },
]


# ── Tool handlers ─────────────────────────────────────────────────────────────

async def _call_tool(name: str, arguments: Dict[str, Any]) -> str:
    """Dispatch a tool call and return a JSON string result."""
    try:
        if name == "get_epic_status":
            from app.routers.status import _fetch_status_data, get_status
            from app.cache import cache
            from app.config import settings
            from app.helpers import compute_health_score, make_meta, now_iso, parse_component
            from app.models import OverallIndicator, StatusBlock

            raw = await _fetch_status_data()
            if not raw:
                return json.dumps({"error": "Unable to reach Epic Games status API"})
            status_raw = raw.get("status", {})
            components = [parse_component(c) for c in raw.get("components", [])]
            health_score = compute_health_score(components)
            indicator = status_raw.get("indicator", "none")
            return json.dumps({
                "indicator": indicator,
                "description": status_raw.get("description", ""),
                "health_score": health_score,
                "is_healthy": indicator == "none",
                "component_count": len(components),
                "degraded_count": sum(1 for c in components if c.status.value != "operational"),
            })

        elif name == "get_epic_dashboard":
            from app.routers.dashboard import _fetch_all
            from app.helpers import compute_health_score, find_component_by_keywords, parse_component, parse_incident
            from app.models import IncidentStatus

            _EAC_KW = ["anti", "cheat", "eac", "easy anti", "anticheat"]
            raw = await _fetch_all()
            summary_raw = raw.get("summary") or {}
            incidents_raw = raw.get("incidents") or {}
            free_raw = raw.get("free_games") or {}

            status = summary_raw.get("status", {})
            components = [parse_component(c) for c in summary_raw.get("components", [])]
            all_incidents = [parse_incident(i) for i in incidents_raw.get("incidents", [])]
            active = [i for i in all_incidents if i.status != IncidentStatus.resolved]
            eac = find_component_by_keywords(components, _EAC_KW)

            from app.routers.free_games import _parse_games
            current_free, _ = _parse_games(free_raw) if free_raw else ([], [])

            return json.dumps({
                "indicator": status.get("indicator", "none"),
                "health_score": compute_health_score(components),
                "is_healthy": status.get("indicator", "none") == "none",
                "total_components": len(components),
                "degraded_components": [
                    {"name": c.name, "status": c.status.value}
                    for c in components if c.status.value != "operational"
                ],
                "active_incidents": [
                    {"name": i.name, "impact": i.impact.value, "latest": i.latest_update}
                    for i in active
                ],
                "eac_status": eac.status.value if eac else "unknown",
                "free_games": [
                    {"title": g.title, "ends_in_days": g.days_remaining}
                    for g in current_free
                ],
            })

        elif name == "get_active_incidents":
            from app.client import fetch_json
            from app.config import settings
            from app.helpers import parse_incident
            from app.models import IncidentStatus

            raw = await fetch_json(settings.EPIC_INCIDENTS_URL)
            if not raw:
                return json.dumps({"error": "Unable to reach Epic Games incidents API"})

            impact_filter = arguments.get("impact")
            limit = arguments.get("limit", 10)

            all_inc = [parse_incident(i) for i in raw.get("incidents", [])]
            active = [i for i in all_inc if i.status != IncidentStatus.resolved and not i.resolved_at]
            if impact_filter:
                active = [i for i in active if i.impact.value == impact_filter]
            active = active[:limit]

            return json.dumps({
                "active_count": len(active),
                "incidents": [
                    {
                        "id": i.id,
                        "name": i.name,
                        "impact": i.impact.value,
                        "status": i.status.value,
                        "created_at": i.created_at,
                        "latest_update": i.latest_update,
                        "shortlink": i.shortlink,
                    }
                    for i in active
                ],
            })

        elif name == "get_eac_status":
            from app.client import fetch_json
            from app.config import settings
            from app.helpers import find_component_by_keywords, parse_component, parse_incident

            _EAC_KW = ["anti", "cheat", "eac", "easy anti", "anticheat"]
            summary_raw = await fetch_json(settings.EPIC_STATUS_URL)
            components = [parse_component(c) for c in (summary_raw or {}).get("components", [])]
            eac = find_component_by_keywords(components, _EAC_KW)
            return json.dumps({
                "found": eac is not None,
                "status": eac.status.value if eac else "unknown",
                "component_name": eac.name if eac else None,
            })

        elif name == "get_free_games":
            from app.client import fetch_json
            from app.config import settings
            from app.routers.free_games import _parse_games

            locale = arguments.get("locale", "en-US")
            raw = await fetch_json(settings.EPIC_FREE_GAMES_URL, params={"locale": locale})
            if not raw:
                return json.dumps({"error": "Unable to reach Epic Games Store API"})
            current, upcoming = _parse_games(raw)
            return json.dumps({
                "current_count": len(current),
                "upcoming_count": len(upcoming),
                "current": [
                    {
                        "title": g.title,
                        "description": g.description,
                        "store_url": g.store_url,
                        "days_remaining": g.days_remaining,
                        "hours_remaining": g.hours_remaining,
                        "end_date": g.offer_end_date,
                    }
                    for g in current
                ],
                "upcoming": [
                    {
                        "title": g.title,
                        "starts_in_days": g.days_remaining,
                        "start_date": g.offer_start_date,
                    }
                    for g in upcoming
                ],
            })

        elif name == "get_components":
            from app.client import fetch_json
            from app.config import settings
            from app.helpers import parse_component
            from app.models import ComponentStatus

            raw = await fetch_json(settings.EPIC_COMPONENTS_URL)
            if not raw:
                return json.dumps({"error": "Unable to reach Epic Games components API"})

            components = [parse_component(c) for c in raw.get("components", [])]
            issues_only = arguments.get("issues_only", False)
            search = arguments.get("search", "").lower()

            if issues_only:
                components = [c for c in components if c.status != ComponentStatus.operational]
            if search:
                components = [c for c in components if search in c.name.lower()]

            return json.dumps({
                "total": len(components),
                "components": [
                    {"id": c.id, "name": c.name, "status": c.status.value}
                    for c in components
                ],
            })

        elif name == "get_services":
            from app.client import fetch_json
            from app.config import settings
            from app.helpers import SERVICES, find_component_by_keywords, parse_component
            from app.models import ComponentStatus

            raw = await fetch_json(settings.EPIC_STATUS_URL)
            if not raw:
                return json.dumps({"error": "Unable to reach Epic Games status API"})

            components = [parse_component(c) for c in raw.get("components", [])]
            services = []
            for display_name, slug, keywords in SERVICES:
                comp = find_component_by_keywords(components, keywords)
                services.append({
                    "name": display_name,
                    "slug": slug,
                    "status": comp.status.value if comp else "unknown",
                })
            return json.dumps({
                "services": services,
                "degraded": [s["name"] for s in services if s["status"] not in ("operational", "unknown")],
            })

        elif name == "check_upstream_health":
            from app.routers.upstream import _probe_all
            raw = await _probe_all()
            return json.dumps(raw)

        elif name == "get_status_history":
            from app.database import get_status_history
            limit = arguments.get("limit", 24)
            history = await get_status_history(limit=limit)
            return json.dumps({"history": history, "count": len(history)})

        elif name == "get_eac_history":
            from app.database import get_eac_history
            limit = arguments.get("limit", 20)
            history = await get_eac_history(limit=limit)
            return json.dumps({"history": history, "count": len(history)})

        else:
            return json.dumps({"error": f"Unknown tool: {name}"})

    except Exception as exc:
        logger.exception("Tool %s failed", name)
        return json.dumps({"error": str(exc)})


# ── FastAPI MCP router ────────────────────────────────────────────────────────

try:
    from mcp.server import Server as _McpServer
    from mcp.server.sse import SseServerTransport as _SseTransport
    from mcp import types as mcp_types
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    logger.warning("mcp package not installed — MCP endpoints will use fallback JSON mode")


def _build_mcp_server():
    """Build and configure the MCP Server with tool handlers (mcp v2 API)."""
    server = _McpServer("epic-games-status-api")

    async def handle_list_tools(params):
        return mcp_types.ListToolsResult(
            tools=[
                mcp_types.Tool(
                    name=t["name"],
                    description=t["description"],
                    inputSchema=t["inputSchema"],
                )
                for t in TOOLS
            ]
        )

    async def handle_call_tool(params):
        name = params.name
        arguments = dict(params.arguments) if params.arguments else {}
        result_text = await _call_tool(name, arguments)
        return mcp_types.CallToolResult(
            content=[mcp_types.TextContent(type="text", text=result_text)]
        )

    server.add_request_handler(
        "tools/list",
        mcp_types.ListToolsRequest,
        handle_list_tools,
    )
    server.add_request_handler(
        "tools/call",
        mcp_types.CallToolRequest,
        handle_call_tool,
    )
    return server


def build_mcp_router():
    """
    Build and return a FastAPI router with MCP SSE endpoints.
    Falls back to plain JSON tool listing/calling if mcp package is absent.
    """
    from fastapi import APIRouter, Request
    from fastapi.responses import JSONResponse

    mcp_router = APIRouter(prefix="/mcp", tags=["MCP (Model Context Protocol)"])

    if _MCP_AVAILABLE:
        _server = _build_mcp_server()
        _sse_transport = _SseTransport("/mcp/messages")

        @mcp_router.get(
            "",
            summary="MCP SSE endpoint (connect here)",
            description=(
                "SSE endpoint for the Model Context Protocol. "
                "Connect with any MCP-compatible client (Claude Desktop, Cursor, Continue, etc.).\n\n"
                "**Claude Desktop config** (`claude_desktop_config.json`):\n"
                "```json\n"
                '{"mcpServers": {"epic-games": {"url": "http://localhost:8000/mcp"}}}\n'
                "```"
            ),
        )
        async def mcp_sse(request: Request):
            async with _sse_transport.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await _server.run(
                    streams[0],
                    streams[1],
                    _server.create_initialization_options(),
                )

        @mcp_router.post(
            "/messages",
            summary="MCP message endpoint",
            description="POST endpoint for MCP client messages (used alongside the SSE stream).",
        )
        async def mcp_messages(request: Request):
            await _sse_transport.handle_post_message(
                request.scope, request.receive, request._send
            )

    else:
        # ── Fallback: plain JSON tool API ─────────────────────────────────────
        @mcp_router.get(
            "/tools",
            summary="List available MCP tools (JSON fallback)",
            description="Lists all available tools. Install the `mcp` package for full SSE support.",
        )
        async def list_tools_json():
            return {"tools": TOOLS, "mcp_sse_available": False}

        @mcp_router.post(
            "/tools/{tool_name}",
            summary="Call a tool (JSON fallback)",
        )
        async def call_tool_json(tool_name: str, request: Request):
            body = await request.json() if request.headers.get("content-type") == "application/json" else {}
            result = await _call_tool(tool_name, body)
            return JSONResponse(content=json.loads(result))

    # ── Always available: tools manifest + direct call endpoint ──────────────

    @mcp_router.get(
        "/tools",
        summary="List all MCP tools",
        description="Returns the full tool manifest: name, description, and input schema for every tool.",
    )
    async def list_tools():
        return {
            "tools": TOOLS,
            "count": len(TOOLS),
            "mcp_sse_available": _MCP_AVAILABLE,
            "sse_endpoint": "/mcp",
            "messages_endpoint": "/mcp/messages",
            "usage": {
                "claude_desktop": {
                    "mcpServers": {
                        "epic-games-status": {
                            "url": "http://<your-host>/mcp"
                        }
                    }
                },
                "http_direct": "POST /mcp/call/{tool_name} with JSON body matching the tool's inputSchema",
            },
        }

    @mcp_router.post(
        "/call/{tool_name}",
        summary="Call any MCP tool directly via HTTP",
        description=(
            "Call any tool by name with a JSON body matching its `inputSchema`. "
            "Returns the tool result as JSON. Works without an MCP client — "
            "great for testing, scripting, or direct LLM function calling.\n\n"
            "Example: `POST /mcp/call/get_free_games` with body `{\"locale\": \"en-US\"}`"
        ),
    )
    async def call_tool_direct(
        tool_name: str,
        arguments: dict = None,
    ):
        from fastapi import Body
        from fastapi.responses import JSONResponse
        tool_names = {t["name"] for t in TOOLS}
        if tool_name not in tool_names:
            return JSONResponse(
                status_code=404,
                content={"error": f"Tool '{tool_name}' not found", "available": sorted(tool_names)},
            )
        result = await _call_tool(tool_name, arguments or {})
        return JSONResponse(content={"tool": tool_name, "result": json.loads(result)})

    return mcp_router
