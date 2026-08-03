"""
Shared async HTTP client (httpx) with retry logic and a legitimate User-Agent.
A single client is reused for connection pooling — important at high concurrency.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import httpx

from app.config import settings

# Headers sent on every upstream request
_DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": settings.USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

# Module-level client; created once at startup, closed at shutdown
_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            headers=_DEFAULT_HEADERS,
            timeout=httpx.Timeout(settings.REQUEST_TIMEOUT),
            limits=httpx.Limits(
                max_connections=200,
                max_keepalive_connections=50,
                keepalive_expiry=30,
            ),
            follow_redirects=True,
            http2=False,  # Epic's CDN behaves better over HTTP/1.1
        )
    return _client


async def close_client() -> None:
    global _client
    if _client and not _client.is_closed:
        await _client.aclose()
        _client = None


async def fetch_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    retries: int = 2,
) -> Optional[Dict[str, Any]]:
    """
    GET *url* and return parsed JSON, or None on any error.
    Retries up to *retries* times with an exponential back-off starting at 0.5 s.
    """
    client = get_client()
    last_exc: Optional[Exception] = None

    for attempt in range(retries + 1):
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(0.5 * (2 ** attempt))
        except httpx.HTTPStatusError as exc:
            # 4xx errors are not retried
            if exc.response.status_code < 500:
                return None
            last_exc = exc
            if attempt < retries:
                await asyncio.sleep(0.5 * (2 ** attempt))
        except Exception as exc:
            last_exc = exc
            break

    return None


async def probe_url(url: str) -> Dict[str, Any]:
    """HEAD probe a URL and return status info."""
    client = get_client()
    try:
        resp = await client.head(url, timeout=8.0)
        return {
            "reachable": resp.status_code < 400,
            "status_code": resp.status_code,
            "latency_ms": resp.elapsed.total_seconds() * 1000 if resp.elapsed else None,
        }
    except httpx.TimeoutException:
        return {"reachable": False, "status_code": None, "latency_ms": None, "error": "timeout"}
    except Exception as exc:
        return {"reachable": False, "status_code": None, "latency_ms": None, "error": str(exc)}
