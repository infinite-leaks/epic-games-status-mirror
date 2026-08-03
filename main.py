"""
Epic Games Status API — main entry point.

Run locally:
    python main.py
    # or
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Replit / any cloud platform:
    The PORT environment variable is respected automatically.
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import init_db
from app.landing import LANDING_HTML
from app.mcp_tools import build_mcp_router
from app.routers import (
    components,
    dashboard,
    eac,
    free_games,
    health,
    incidents,
    services,
    status,
    stream,
    upstream,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("epicapi")

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Epic Games Status API v%s", settings.API_VERSION)
    await init_db()
    yield
    from app.client import close_client
    await close_client()
    logger.info("Epic Games Status API shut down cleanly")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    contact={
        "name": settings.API_CONTACT_NAME,
        "url": settings.API_CONTACT_URL,
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache", "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# ── Rate limiting ─────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Request ID + timing middleware ────────────────────────────────────────────
import uuid

@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.monotonic()
    response = await call_next(request)
    duration_ms = round((time.monotonic() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(status.router)
app.include_router(components.router)
app.include_router(incidents.router)
app.include_router(eac.router)
app.include_router(free_games.router)
app.include_router(services.router)
app.include_router(dashboard.router)
app.include_router(upstream.router)
app.include_router(stream.router)
app.include_router(build_mcp_router())


# ── Landing page ──────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing():
    return HTMLResponse(content=LANDING_HTML)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again.",
            "path": str(request.url.path),
        },
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        log_level="info",
        access_log=True,
        # Production-friendly: allow Replit's proxy headers
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
