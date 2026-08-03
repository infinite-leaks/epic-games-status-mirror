"""
HTML landing page served at GET /
Rich, dark-themed page with full endpoint reference.
"""

LANDING_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Epic Games Status API</title>
<style>
  :root {
    --bg: #0d1117; --bg2: #161b22; --bg3: #21262d;
    --border: #30363d; --text: #e6edf3; --muted: #8b949e;
    --blue: #58a6ff; --green: #3fb950; --yellow: #d29922;
    --red: #f85149; --purple: #bc8cff; --orange: #ffa657;
    --cyan: #76e3ea;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; }
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: var(--bg3); border: 1px solid var(--border); padding: 1px 6px; border-radius: 4px; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.85em; }
  pre { background: var(--bg3); border: 1px solid var(--border); border-radius: 8px; padding: 16px; overflow-x: auto; }
  pre code { background: none; border: none; padding: 0; font-size: 0.88em; }

  header { background: var(--bg2); border-bottom: 1px solid var(--border); padding: 24px 0; }
  .header-inner { max-width: 1100px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  .logo { font-size: 1.6rem; font-weight: 700; }
  .logo span { color: var(--blue); }
  .badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }
  .badge-green { background: rgba(63,185,80,.15); color: var(--green); border: 1px solid rgba(63,185,80,.3); }
  .badge-blue  { background: rgba(88,166,255,.15); color: var(--blue);  border: 1px solid rgba(88,166,255,.3); }
  .header-links { margin-left: auto; display: flex; gap: 12px; }
  .btn { padding: 6px 14px; border-radius: 6px; font-size: 0.85rem; font-weight: 500; display: inline-flex; align-items: center; gap: 6px; }
  .btn-primary { background: var(--blue); color: #000; }
  .btn-outline { border: 1px solid var(--border); color: var(--text); }
  .btn:hover { opacity: .85; text-decoration: none; }

  main { max-width: 1100px; margin: 0 auto; padding: 48px 24px; }

  .hero { text-align: center; margin-bottom: 56px; }
  .hero h1 { font-size: 2.4rem; font-weight: 800; margin-bottom: 12px; }
  .hero h1 span { color: var(--blue); }
  .hero p { color: var(--muted); font-size: 1.1rem; max-width: 600px; margin: 0 auto 24px; }
  .hero-badges { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 48px; }
  .card { background: var(--bg2); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }
  .card h3 { font-size: 0.9rem; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
  .card p { color: var(--muted); font-size: 0.85rem; }

  .section { margin-bottom: 48px; }
  .section h2 { font-size: 1.3rem; font-weight: 700; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 8px; }

  table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
  th { background: var(--bg3); text-align: left; padding: 10px 14px; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
  td { padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .method { font-weight: 700; font-size: 0.8rem; padding: 2px 8px; border-radius: 4px; display: inline-block; }
  .get   { background: rgba(63,185,80,.15); color: var(--green); }
  .post  { background: rgba(255,166,87,.15); color: var(--orange); }
  .tag-mcp    { background: rgba(188,140,255,.15); color: var(--purple); }
  .tag-sse    { background: rgba(118,227,234,.15); color: var(--cyan); }
  .endpoint-path { color: var(--blue); font-family: monospace; }

  .highlight-box { background: var(--bg2); border: 1px solid var(--border); border-left: 3px solid var(--blue); border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; }
  .highlight-box h4 { font-size: 0.9rem; margin-bottom: 8px; }
  .highlight-box p  { color: var(--muted); font-size: 0.85rem; }

  footer { border-top: 1px solid var(--border); padding: 24px; text-align: center; color: var(--muted); font-size: 0.85rem; }

  @media (max-width: 640px) {
    .hero h1 { font-size: 1.7rem; }
    table { display: block; overflow-x: auto; }
    .header-links { display: none; }
  }
</style>
</head>
<body>

<header>
  <div class="header-inner">
    <div class="logo">Epic Games <span>Status API</span></div>
    <span class="badge badge-green">● Live</span>
    <span class="badge badge-blue">v1.0.0</span>
    <div class="header-links">
      <a href="/docs" class="btn btn-primary">📖 Swagger UI</a>
      <a href="/redoc" class="btn btn-outline">ReDoc</a>
      <a href="/openapi.json" class="btn btn-outline">openapi.json</a>
      <a href="/mcp/tools" class="btn btn-outline">🤖 MCP Tools</a>
    </div>
  </div>
</header>

<main>
  <div class="hero">
    <h1>Epic Games <span>Status API</span></h1>
    <p>Production-grade REST + MCP API for Epic Games service status, incidents, Easy Anti-Cheat monitoring, free games tracking, and more.</p>
    <div class="hero-badges">
      <span class="badge badge-green">CORS Enabled</span>
      <span class="badge badge-blue">OpenAPI 3.1</span>
      <span class="badge badge-blue">MCP Tools</span>
      <span class="badge badge-blue">SSE Stream</span>
      <span class="badge badge-blue">SQLite History</span>
      <span class="badge badge-blue">100k+ req/s ready</span>
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h3>🎮 Service Status</h3>
      <p>Real-time status for Fortnite, Store, Login, Matchmaking, EAC, Rocket League, Fall Guys and more with health scores.</p>
    </div>
    <div class="card">
      <h3>🚨 Incidents</h3>
      <p>Active and resolved incidents with impact levels, timelines, and duration tracking stored in SQLite.</p>
    </div>
    <div class="card">
      <h3>🛡️ Easy Anti-Cheat</h3>
      <p>Dedicated EAC monitoring with change detection, history log, and incident correlation.</p>
    </div>
    <div class="card">
      <h3>🎁 Free Games</h3>
      <p>Current and upcoming Epic Games Store free games with countdown timers, cover images, and store links.</p>
    </div>
    <div class="card">
      <h3>🤖 MCP Tools</h3>
      <p>Full Model Context Protocol server. Connect Claude Desktop, Cursor, or any MCP-compatible agent.</p>
    </div>
    <div class="card">
      <h3>📡 SSE Stream</h3>
      <p>Server-Sent Events live stream — subscribe once and receive status updates without polling.</p>
    </div>
  </div>

  <!-- Quick Start -->
  <div class="section">
    <h2>⚡ Quick Start</h2>
    <div class="highlight-box">
      <h4>Overall status (3 lines)</h4>
      <pre><code>curl https://your-api.com/v1/status</code></pre>
    </div>
    <div class="highlight-box">
      <h4>Full dashboard (everything in one call)</h4>
      <pre><code>curl https://your-api.com/v1/dashboard</code></pre>
    </div>
    <div class="highlight-box">
      <h4>Connect Claude Desktop to MCP</h4>
      <pre><code>{
  "mcpServers": {
    "epic-games-status": {
      "url": "https://your-api.com/mcp"
    }
  }
}</code></pre>
    </div>
    <div class="highlight-box">
      <h4>Live SSE stream (JavaScript)</h4>
      <pre><code>const es = new EventSource('https://your-api.com/v1/stream');
es.onmessage = e => {
  const data = JSON.parse(e.data);
  console.log(`Health: ${data.health_score}/100 | Incidents: ${data.active_incidents}`);
};</code></pre>
    </div>
  </div>

  <!-- API Endpoints -->
  <div class="section">
    <h2>📋 API Endpoints</h2>
    <table>
      <thead>
        <tr>
          <th>Method</th><th>Endpoint</th><th>Description</th>
        </tr>
      </thead>
      <tbody>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/status" class="endpoint-path">/v1/status</a></td><td>Overall Epic Games status with health score (0–100)</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/status/summary" class="endpoint-path">/v1/status/summary</a></td><td>Full status summary (components + incidents)</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/status/history" class="endpoint-path">/v1/status/history</a></td><td>Historical status snapshots from local DB</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/components" class="endpoint-path">/v1/components</a></td><td>All Epic service components with filtering</td></tr>
        <tr><td><span class="method get">GET</span></td><td><span class="endpoint-path">/v1/components/{id}</span></td><td>Single component by ID</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/incidents" class="endpoint-path">/v1/incidents</a></td><td>All incidents (active + resolved)</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/incidents/active" class="endpoint-path">/v1/incidents/active</a></td><td>Active incidents only</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/incidents/history" class="endpoint-path">/v1/incidents/history</a></td><td>Incident history from local DB</td></tr>
        <tr><td><span class="method get">GET</span></td><td><span class="endpoint-path">/v1/incidents/{id}</span></td><td>Single incident with full update timeline</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/eac" class="endpoint-path">/v1/eac</a></td><td>Easy Anti-Cheat status + change detection</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/eac/history" class="endpoint-path">/v1/eac/history</a></td><td>EAC status change history</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/free-games" class="endpoint-path">/v1/free-games</a></td><td>Current and upcoming free games</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/free-games/current" class="endpoint-path">/v1/free-games/current</a></td><td>Currently free games only</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/free-games/upcoming" class="endpoint-path">/v1/free-games/upcoming</a></td><td>Upcoming free games only</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/services" class="endpoint-path">/v1/services</a></td><td>Curated key services (Fortnite, Store, Login…)</td></tr>
        <tr><td><span class="method get">GET</span></td><td><span class="endpoint-path">/v1/services/{slug}</span></td><td>Single service by slug</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/dashboard" class="endpoint-path">/v1/dashboard</a></td><td>🔥 Full dashboard — all data in one call</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/v1/upstream" class="endpoint-path">/v1/upstream</a></td><td>Probe upstream Epic API endpoints</td></tr>
        <tr><td><span class="method get">GET</span></td><td><span class="endpoint-path tag-sse">/v1/stream</span></td><td>📡 Live SSE status stream</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/mcp/tools" class="endpoint-path tag-mcp">/mcp/tools</a></td><td>🤖 MCP tool manifest</td></tr>
        <tr><td><span class="method get">GET</span></td><td><span class="endpoint-path tag-mcp">/mcp</span></td><td>🤖 MCP SSE endpoint (connect agents here)</td></tr>
        <tr><td><span class="method post">POST</span></td><td><span class="endpoint-path tag-mcp">/mcp/call/{tool}</span></td><td>🤖 Call any MCP tool directly via HTTP</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/health" class="endpoint-path">/health</a></td><td>API liveness check + cache stats</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/ping" class="endpoint-path">/ping</a></td><td>Minimal liveness probe</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/docs" class="endpoint-path">/docs</a></td><td>Swagger UI interactive docs</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/redoc" class="endpoint-path">/redoc</a></td><td>ReDoc documentation</td></tr>
        <tr><td><span class="method get">GET</span></td><td><a href="/openapi.json" class="endpoint-path">/openapi.json</a></td><td>Raw OpenAPI 3.1 specification</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Query Parameters -->
  <div class="section">
    <h2>🎛️ Common Query Parameters</h2>
    <table>
      <thead><tr><th>Parameter</th><th>Type</th><th>Default</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td><code>force_refresh</code></td><td>boolean</td><td>false</td><td>Bypass cache and fetch live data from Epic</td></tr>
        <tr><td><code>active_only</code></td><td>boolean</td><td>false</td><td>Return only unresolved incidents</td></tr>
        <tr><td><code>impact</code></td><td>string</td><td>—</td><td>Filter incidents by impact: none, minor, major, critical</td></tr>
        <tr><td><code>issues_only</code></td><td>boolean</td><td>false</td><td>Return only degraded components</td></tr>
        <tr><td><code>search</code></td><td>string</td><td>—</td><td>Case-insensitive substring search on component/service names</td></tr>
        <tr><td><code>limit</code></td><td>integer</td><td>20</td><td>Max results to return (varies per endpoint)</td></tr>
        <tr><td><code>locale</code></td><td>string</td><td>en-US</td><td>Locale for free games titles (de-DE, fr-FR, ja-JP, etc.)</td></tr>
        <tr><td><code>interval</code></td><td>integer</td><td>30</td><td>Seconds between SSE updates (10–300)</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Response shape -->
  <div class="section">
    <h2>📦 Response Shape</h2>
    <p style="color:var(--muted); margin-bottom:16px;">Every response includes a <code>meta</code> block and a plain-text <code>summary</code> field ideal for LLM consumption.</p>
    <pre><code>{
  "status": { "indicator": "none", "description": "All Systems Operational" },
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
}</code></pre>
  </div>

  <!-- MCP -->
  <div class="section">
    <h2>🤖 MCP Tools Reference</h2>
    <p style="color:var(--muted);margin-bottom:16px;">All 10 tools are also callable directly via <code>POST /mcp/call/{tool_name}</code> — no MCP client needed.</p>
    <table>
      <thead><tr><th>Tool</th><th>Description</th></tr></thead>
      <tbody>
        <tr><td><code>get_epic_status</code></td><td>Quick overall status + health score</td></tr>
        <tr><td><code>get_epic_dashboard</code></td><td>Full dashboard — all data in one call</td></tr>
        <tr><td><code>get_active_incidents</code></td><td>Active incidents with impact filtering</td></tr>
        <tr><td><code>get_eac_status</code></td><td>Easy Anti-Cheat status + change flag</td></tr>
        <tr><td><code>get_free_games</code></td><td>Current + upcoming free games with countdowns</td></tr>
        <tr><td><code>get_components</code></td><td>All components with issues_only filter</td></tr>
        <tr><td><code>get_services</code></td><td>Curated service health list</td></tr>
        <tr><td><code>check_upstream_health</code></td><td>Probe all Epic upstream APIs</td></tr>
        <tr><td><code>get_status_history</code></td><td>Historical status snapshots</td></tr>
        <tr><td><code>get_eac_history</code></td><td>EAC change history log</td></tr>
      </tbody>
    </table>
  </div>

  <!-- Rate limits & caching -->
  <div class="section">
    <h2>⚙️ Caching & Rate Limits</h2>
    <div class="grid">
      <div class="card">
        <h3>🗃️ In-Process TTL Cache</h3>
        <p>Status: 30 s · Incidents: 60 s · Free Games: 300 s · Upstream probes: 60 s. Bypassed with <code>?force_refresh=true</code>.</p>
      </div>
      <div class="card">
        <h3>🛡️ Rate Limits</h3>
        <p>300 req/min per IP on most endpoints. 60 req/min on <code>/v1/dashboard</code>. Configurable via <code>RATE_LIMIT_DEFAULT</code> env var.</p>
      </div>
      <div class="card">
        <h3>📊 SQLite History</h3>
        <p>Status checks, incidents, and EAC changes are persisted to <code>data/history.db</code> across restarts.</p>
      </div>
    </div>
  </div>

</main>

<footer>
  Epic Games Status API v1.0.0 &mdash; Not affiliated with Epic Games, Inc. &mdash;
  <a href="/docs">Swagger</a> &middot;
  <a href="/openapi.json">OpenAPI</a> &middot;
  <a href="/mcp/tools">MCP</a> &middot;
  <a href="https://github.com/ynwglobal/epic-games-status-monitor">GitHub</a>
</footer>

</body>
</html>
"""
