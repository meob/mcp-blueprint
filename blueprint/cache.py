"""Lightweight in-memory cache.

A per-TTL :class:`cachetools.TTLCache` is maintained for each distinct TTL
declared by tools.  Caching is optional and fully transparent: a tool with no
TTL is never cached.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import Any

from cachetools import TTLCache

CacheKey = tuple[Hashable, ...]


class Cache:
    """Thread-safe TTL cache keyed by ``(tool_name, params)``."""

    def __init__(self, maxsize: int = 256) -> None:
        self._maxsize = maxsize
        self._caches: dict[int, TTLCache[CacheKey, Any]] = {}

    def _cache_for(self, ttl: int) -> TTLCache[CacheKey, Any]:
        if ttl not in self._caches:
            self._caches[ttl] = TTLCache(maxsize=self._maxsize, ttl=ttl)
        return self._caches[ttl]

    def get(self, key: CacheKey) -> Any | None:
        """Return the cached value or ``None`` when absent or expired."""
        for cache in self._caches.values():
            value = cache.get(key)
            if value is not None:
                return value
        return None

    def set(self, key: CacheKey, value: Any, ttl: int) -> None:
        """Store ``value`` under ``key`` with the given TTL in seconds."""
        self._cache_for(ttl)[key] = value

    def clear(self) -> None:
        """Remove all cached entries."""
        for cache in self._caches.values():
            cache.clear()
        self._caches.clear()
