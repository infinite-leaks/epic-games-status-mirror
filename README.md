# Epic Games Status API 🎮

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-orange.svg)](https://swagger.io/specification/)
[![MCP](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple.svg)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A **production-grade REST + MCP API** for Epic Games service status, incidents, Easy Anti-Cheat monitoring, free games tracking, and more. Built with FastAPI, async throughout, handles 100k+ concurrent users via TTL caching.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎮 **Service Status** | Real-time status for Fortnite, Store, Login, Matchmaking, EAC, Rocket League, Fall Guys with 0–100 health score |
| 🚨 **Incident Tracking** | Active + resolved incidents, impact levels, full update timelines, duration tracking |
| 🛡️ **EAC Monitoring** | Dedicated Easy Anti-Cheat endpoint with change detection alerts and history log |
| 🎁 **Free Games** | Current + upcoming Epic Games Store free games, countdown timers, cover images, store URLs |
| 🤖 **MCP Tools** | Full Model Context Protocol server — connect Claude Desktop, Cursor, Continue, or any MCP agent |
| 📡 **SSE Stream** | Server-Sent Events live stream — subscribe once, receive updates without polling |
| 📊 **SQLite History** | Status, incident, and EAC changes persisted across restarts |
| ⚡ **High Performance** | Async httpx + in-process TTL cache + GZip — safe for 1–100k concurrent users |
| 🌐 **CORS Enabled** | Wildcard CORS by default, configurable per-origin via env var |
| 📖 **Swagger UI** | Interactive docs at `/docs`, ReDoc at `/redoc`, raw spec at `/openapi.json` |
| 🏠 **Rich Landing Page** | Full dark-themed API reference page at `/` |

---

## 🚀 Quick Start

### Hosting: Local / Any Hosting

```bash
# Clone
git clone https://github.com/ynwglobal/epic-games-status-monitor.git
cd epic-games-status-monitor

# Install dependencies
pip install -r requirements.txt

# Run
python main.py
# API is now live at http://localhost:8000
```

### Option 3: Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
```

### Option 4: Any Cloud (Railway, Render, Fly.io, Heroku, etc.)

Set the `PORT` environment variable — the API reads it automatically.

```bash
# Render / Railway start command:
python main.py

# Heroku Procfile:
web: python main.py
```

---

## 📋 API Endpoints

### Status

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/status` | Overall Epic Games status + health score (0–100) |
| `GET` | `/v1/status/summary` | Full status summary (all components + current incidents) |
| `GET` | `/v1/status/history` | Historical status snapshots from local DB |

### Components

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/components` | All components with `?status=`, `?search=`, `?issues_only=true` filtering |
| `GET` | `/v1/components/{id}` | Single component by ID |

### Incidents

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/incidents` | All incidents (active + resolved) |
| `GET` | `/v1/incidents/active` | Active incidents only |
| `GET` | `/v1/incidents/history` | Incident history from local DB |
| `GET` | `/v1/incidents/{id}` | Single incident with full update timeline |

### Easy Anti-Cheat

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/eac` | EAC status + change detection + related incidents |
| `GET` | `/v1/eac/history` | EAC status change history |

### Free Games

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/free-games` | Current + upcoming free games |
| `GET` | `/v1/free-games/current` | Currently free games only |
| `GET` | `/v1/free-games/upcoming` | Upcoming free games only |

### Services & Dashboard

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/services` | Curated key services (Fortnite, Store, Login, Matchmaking…) |
| `GET` | `/v1/services/{slug}` | Single service by slug |
| `GET` | `/v1/dashboard` | 🔥 Full dashboard — all data in one concurrent call |
| `GET` | `/v1/upstream` | Probe all Epic upstream API endpoints |

### Live Stream

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/v1/stream` | Server-Sent Events live status stream |

### MCP (Model Context Protocol)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/mcp` | SSE endpoint for MCP clients |
| `POST` | `/mcp/messages` | MCP message endpoint |
| `GET` | `/mcp/tools` | List all available MCP tools |
| `POST` | `/mcp/call/{tool_name}` | Call any tool directly via HTTP |

### API Internals

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | API liveness + cache stats |
| `GET` | `/ping` | Minimal liveness probe |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc docs |
| `GET` | `/openapi.json` | Raw OpenAPI 3.1 specification |

---

## 🎛️ Query Parameters

All endpoints support these common parameters:

| Parameter | Type | Default | Description |
|---|---|---|---|
| `force_refresh` | boolean | false | Bypass cache and fetch live data from Epic |
| `active_only` | boolean | false | Return only unresolved incidents |
| `impact` | string | — | Filter incidents: `none`, `minor`, `major`, `critical` |
| `issues_only` | boolean | false | Return only degraded/outage components |
| `search` | string | — | Case-insensitive substring search |
| `limit` | integer | 20 | Max results (varies per endpoint) |
| `locale` | string | en-US | Locale for free games (de-DE, fr-FR, ja-JP…) |
| `interval` | integer | 30 | SSE update interval in seconds (10–300) |

---

## 📦 Response Format

Every response includes:

```json
{
  "status": {
    "indicator": "none",
    "description": "All Systems Operational"
  },
  "health_score": 97,
  "is_healthy": true,
  "summary": "✅ All Epic Games services are operational. Health score: 97/100.",
  "meta": {
    "cached": true,
    "cache_ttl_seconds": 30,
    "fetched_at": "2026-08-03T12:00:00+00:00",
    "next_poll_at": "2026-08-03T12:00:30+00:00",
    "api_version": "1.0.0"
  }
}
```

- **`summary`** — plain-text description ideal for LLM consumption, quick UIs, or alerts
- **`meta.cached`** — whether this came from the API's in-process cache
- **`meta.next_poll_at`** — when you should poll again for fresh data
- **`health_score`** — numeric 0–100 score (100 = all operational)

---

## 🤖 MCP Integration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "epic-games-status": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|---|---|
| `get_epic_status` | Quick overall status + health score |
| `get_epic_dashboard` | Full dashboard — all data in one call |
| `get_active_incidents` | Active incidents with impact filter |
| `get_eac_status` | EAC status + change detection flag |
| `get_free_games` | Current + upcoming free games |
| `get_components` | All components with `issues_only` filter |
| `get_services` | Curated service health list |
| `check_upstream_health` | Probe all Epic upstream APIs |
| `get_status_history` | Historical status snapshots |
| `get_eac_history` | EAC change history log |

### Direct HTTP Tool Calls (no MCP client needed)

```bash
# Call any tool directly
curl -X POST http://localhost:8000/mcp/call/get_epic_dashboard

curl -X POST http://localhost:8000/mcp/call/get_free_games \
  -H "Content-Type: application/json" \
  -d '{"locale": "de-DE"}'

curl -X POST http://localhost:8000/mcp/call/get_active_incidents \
  -H "Content-Type: application/json" \
  -d '{"impact": "critical", "limit": 5}'
```

---

## 📡 Server-Sent Events (SSE) Stream

Subscribe once and receive live updates:

```javascript
// Browser
const es = new EventSource('https://your-api.com/v1/stream?interval=30');
es.onmessage = e => {
  const data = JSON.parse(e.data);
  console.log(`Health: ${data.health_score}/100 | Incidents: ${data.active_incidents}`);
};

// Node.js / fetch
const res = await fetch('https://your-api.com/v1/stream');
for await (const chunk of res.body) {
  const line = new TextDecoder().decode(chunk);
  if (line.startsWith('data:')) {
    console.log(JSON.parse(line.slice(5)));
  }
}
```

Stream payload:
```json
{
  "event": "status_update",
  "timestamp": "2026-08-03T12:00:00+00:00",
  "indicator": "none",
  "health_score": 97,
  "active_incidents": 0,
  "is_healthy": true
}
```

---

## ⚙️ Configuration

All settings are driven by environment variables. Copy `.env.example` to `.env` and customize:

```bash
# Server
PORT=8000
WORKERS=1

# Cache TTLs (seconds)
CACHE_TTL_STATUS=30
CACHE_TTL_INCIDENTS=60
CACHE_TTL_FREE_GAMES=300

# Rate limiting
RATE_LIMIT_DEFAULT=300/minute

# CORS (comma-separated, * = all origins)
CORS_ORIGINS=["*"]

# SQLite history DB path
DATABASE_PATH=data/history.db
```

---

## 🏗️ Architecture

```
main.py                  ← FastAPI app + middleware + startup
app/
  config.py              ← Pydantic-settings driven config
  cache.py               ← Async in-process TTL cache (stampede protection)
  client.py              ← Shared httpx async client (connection pool)
  models.py              ← Pydantic v2 response models (used in OpenAPI spec)
  helpers.py             ← Shared parsing utilities + SERVICES map
  database.py            ← aiosqlite history persistence
  landing.py             ← HTML landing page
  mcp_tools.py           ← MCP server + 10 tool definitions
  routers/
    status.py            ← /v1/status
    components.py        ← /v1/components
    incidents.py         ← /v1/incidents
    eac.py               ← /v1/eac
    free_games.py        ← /v1/free-games
    services.py          ← /v1/services
    dashboard.py         ← /v1/dashboard (concurrent fetch)
    upstream.py          ← /v1/upstream
    stream.py            ← /v1/stream (SSE)
    health.py            ← /health + /ping
```

### Performance Design

- **Single cache entry per endpoint** shared across all concurrent requests — 100k users hitting `/v1/status` cost one Epic API call per TTL window
- **Per-key asyncio locks** prevent cache stampedes under burst traffic
- **Connection pool** via `httpx.AsyncClient` (200 max connections) — no per-request TCP overhead
- **GZip compression** on responses ≥ 1KB
- **Async throughout** — no blocking I/O, all database and HTTP calls are awaited

---

## 🔌 Deployment Checklist

- [ ] `pip install -r requirements.txt`
- [ ] Set `PORT` environment variable (auto-detected on Replit, Railway, Render, Heroku, Fly.io)
- [ ] Optional: set `CORS_ORIGINS` to restrict allowed origins in production
- [ ] Optional: set `WORKERS=1` (use 1 worker with the in-process cache, or add Redis for multi-worker setups)
- [ ] Verify `/health` returns `{"status": "ok"}`
- [ ] Verify `/docs` loads Swagger UI

---

## 📊 Monitoring Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /ping` | Kubernetes liveness probe (no deps) |
| `GET /health` | Readiness probe + cache stats |
| `GET /v1/upstream` | Checks Epic API reachability |

---

## 📚 Code Examples

### Python

```python
import httpx

async with httpx.AsyncClient() as client:
    # Full dashboard
    r = await client.get("http://localhost:8000/v1/dashboard")
    data = r.json()
    print(f"Health: {data['health_score']}/100")
    print(f"Free games: {[g['title'] for g in data['current_free_games']]}")
```

### JavaScript / TypeScript

```typescript
const res = await fetch('http://localhost:8000/v1/dashboard');
const data = await res.json();
console.log(data.summary); // "✅ All Epic Games services are operational."
```

### curl

```bash
# Health check
curl http://localhost:8000/health

# Active incidents only
curl "http://localhost:8000/v1/incidents?active_only=true&impact=critical"

# Force fresh data (bypass cache)
curl "http://localhost:8000/v1/status?force_refresh=true"

# Free games in German
curl "http://localhost:8000/v1/free-games?locale=de-DE"

# Service slugs available
curl http://localhost:8000/v1/services | jq '[.services[].slug]'
```

---

## ⚠️ Disclaimer

This tool uses Epic Games' **public** status APIs and is **not affiliated with, endorsed by, or sponsored by Epic Games, Inc.** Fortnite, Epic Games Store and Easy Anti-Cheat are trademarks of their respective owners. Respect API rate limits — the in-process cache ensures polite upstream usage.

---

## 📝 License

MIT — see [LICENSE](LICENSE) for details.

---

**Made with ❤️ for developers, LLMs, and the Epic Games community**
