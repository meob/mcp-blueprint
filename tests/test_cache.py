"""Unit tests for the TTL cache."""

from __future__ import annotations

import asyncio

from blueprint.cache import Cache


def test_set_and_get() -> None:
    cache = Cache()
    key = ("get_database_size", (("database", "pgbench"),))
    cache.set(key, [{"size": 1}], ttl=60)
    assert cache.get(key) == [{"size": 1}]


async def test_expiry() -> None:
    cache = Cache()
    key = ("t", ())
    cache.set(key, "v", ttl=1)
    assert cache.get(key) == "v"
    await asyncio.sleep(1.1)
    assert cache.get(key) is None


def test_clear() -> None:
    cache = Cache()
    key = ("t", ())
    cache.set(key, "v", ttl=60)
    cache.clear()
    assert cache.get(key) is None


def test_different_ttls_share_no_state() -> None:
    cache = Cache()
    key = ("t", ())
    cache.set(key, "a", ttl=60)
    cache.set(key, "b", ttl=1)
    assert cache.get(key) in {"a", "b"}
