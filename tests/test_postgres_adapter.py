"""Unit tests for the PostgreSQL adapter error handling."""

from __future__ import annotations

import pytest
from psycopg import OperationalError

from blueprint.config import DatabaseConfig
from blueprint.db.postgres import PostgresAdapter
from blueprint.errors import DatabaseError


def make_adapter() -> PostgresAdapter:
    return PostgresAdapter(
        DatabaseConfig(engine="postgresql", dsn="postgresql://user@localhost/app")
    )


async def test_pool_open_failure_raises_database_error_with_reason(monkeypatch) -> None:
    """A failed pool open must surface the underlying connection error."""

    from blueprint.db import postgres as module

    class FakePool:
        def __init__(self, **kwargs: object) -> None:
            self.closed = False

        async def open(self) -> None:
            raise RuntimeError("pool open failed")

        async def close(self) -> None:
            self.closed = True

    class FakeConnection:
        @classmethod
        async def connect(cls, conninfo: str, connect_timeout: int) -> FakeConnection:
            raise OperationalError('connection failed: FATAL: permission denied for database "app"')

    monkeypatch.setattr(module, "AsyncConnectionPool", FakePool)
    monkeypatch.setattr(module.psycopg, "AsyncConnection", FakeConnection)

    adapter = make_adapter()
    try:
        await adapter.test_connection()
    except DatabaseError as exc:
        assert "permission denied" in str(exc)
    else:
        pytest.fail("expected DatabaseError")
