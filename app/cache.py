"""
Async in-process TTL cache.

Design rationale
────────────────
• A single asyncio.Lock per key prevents cache stampedes under high concurrency.
• Values are stored with an expiry timestamp so no background thread is needed.
• At 100 k req/s the cache is the primary shield in front of Epic's APIs;
  every cache HIT avoids a round-trip and keeps the API fast.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, Optional, Tuple


class _Entry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float) -> None:
        self.value = value
        self.expires_at = time.monotonic() + ttl


class AsyncTTLCache:
    """Thread-safe (asyncio-safe), in-process cache with per-key TTL."""

    def __init__(self) -> None:
        self._store: Dict[str, _Entry] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._meta: Dict[str, Dict] = {}  # stores hit/miss counts per key

    def _get_lock(self, key: str) -> asyncio.Lock:
        if key not in self._locks:
            self._locks[key] = asyncio.Lock()
        return self._locks[key]

    def get(self, key: str) -> Tuple[bool, Any]:
        """Return (hit, value). Expired entries count as misses."""
        entry = self._store.get(key)
        if entry is None:
            return False, None
        if time.monotonic() > entry.expires_at:
            del self._store[key]
            return False, None
        meta = self._meta.setdefault(key, {"hits": 0, "misses": 0})
        meta["hits"] += 1
        return True, entry.value

    def set(self, key: str, value: Any, ttl: float) -> None:
        self._store[key] = _Entry(value, ttl)
        meta = self._meta.setdefault(key, {"hits": 0, "misses": 0})
        meta["misses"] += 1  # count as miss (fresh fetch)

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        keys = [k for k in self._store if k.startswith(prefix)]
        for k in keys:
            del self._store[k]

    def stats(self) -> Dict[str, Any]:
        now = time.monotonic()
        alive = {k for k, v in self._store.items() if v.expires_at > now}
        return {
            "cached_keys": len(alive),
            "total_keys_ever": len(self._meta),
            "per_key": self._meta,
        }

    async def get_or_fetch(
        self,
        key: str,
        ttl: float,
        fetch_fn: Callable[[], Any],
    ) -> Any:
        """
        Return cached value if still valid; otherwise call *fetch_fn* (async or
        sync), cache the result for *ttl* seconds, and return it.

        Uses a per-key lock so only one coroutine fetches at a time even if
        hundreds of requests arrive simultaneously for the same key.
        """
        hit, value = self.get(key)
        if hit:
            return value

        async with self._get_lock(key):
            # Re-check after acquiring lock (another coroutine may have filled it)
            hit, value = self.get(key)
            if hit:
                return value

            if asyncio.iscoroutinefunction(fetch_fn):
                value = await fetch_fn()
            else:
                value = fetch_fn()

            if value is not None:
                self.set(key, value, ttl)
            return value


# Singleton used across the whole app
cache = AsyncTTLCache()
