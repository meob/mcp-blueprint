"""Lightweight in-memory cache.

A per-TTL :class:`cachetools.TTLCache` is maintained for each distinct TTL
declared by tools.  Caching is optional and fully transparent: a tool with no
TTL is never cached.  When a :class:`~blueprint.metrics.Metrics` instance is
injected, the cache keeps the size gauges current.
"""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, Any

from cachetools import TTLCache

if TYPE_CHECKING:
    from blueprint.metrics import Metrics

CacheKey = tuple[Hashable, ...]


class Cache:
    """Thread-safe TTL cache keyed by ``(tool_name, params)``."""

    def __init__(self, maxsize: int = 256, metrics: Metrics | None = None) -> None:
        self._maxsize = maxsize
        self._metrics = metrics
        self._caches: dict[int, TTLCache[CacheKey, Any]] = {}
        if metrics is not None:
            metrics.set_cache_stats(entries=0, maxsize=maxsize)

    def _cache_for(self, ttl: int) -> TTLCache[CacheKey, Any]:
        if ttl not in self._caches:
            self._caches[ttl] = TTLCache(maxsize=self._maxsize, ttl=ttl)
        return self._caches[ttl]

    def _refresh_gauges(self) -> None:
        if self._metrics is not None:
            entries = sum(len(cache) for cache in self._caches.values())
            self._metrics.set_cache_stats(entries=entries, maxsize=self._maxsize)

    def get(self, key: CacheKey) -> Any | None:
        """Return the cached value or ``None`` when absent or expired."""
        for cache in self._caches.values():
            value = cache.get(key)
            if value is not None:
                self._refresh_gauges()
                return value
        self._refresh_gauges()
        return None

    def set(self, key: CacheKey, value: Any, ttl: int) -> None:
        """Store ``value`` under ``key`` with the given TTL in seconds."""
        self._cache_for(ttl)[key] = value
        self._refresh_gauges()

    def clear(self) -> None:
        """Remove all cached entries."""
        for cache in self._caches.values():
            cache.clear()
        self._caches.clear()
        self._refresh_gauges()
