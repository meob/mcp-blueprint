"""PostgreSQL adapter built on psycopg3 async connection pool."""

from __future__ import annotations

import asyncio
from typing import Any

import psycopg
import structlog
from psycopg_pool import AsyncConnectionPool

from blueprint.config import DatabaseConfig
from blueprint.db.base import DatabaseAdapter
from blueprint.errors import DatabaseError

logger = structlog.get_logger(__name__)

#: Bounded wait for the initial pool open so connection failures surface
#: quickly instead of hanging for the full runtime pool timeout.
_POOL_OPEN_TIMEOUT = 10.0


class PostgresAdapter(DatabaseAdapter):
    """Async PostgreSQL adapter using an :class:`AsyncConnectionPool`.

    Connections are pooled, never created per request.
    """

    engine = "postgresql"

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._pool: AsyncConnectionPool | None = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> AsyncConnectionPool:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    self._pool = AsyncConnectionPool(
                        conninfo=self._config.resolved_dsn,
                        min_size=self._config.pool.min_size,
                        max_size=self._config.pool.max_size,
                        timeout=self._config.pool.timeout,
                        open=False,
                    )
                    try:
                        await self._pool.open(wait=True, timeout=_POOL_OPEN_TIMEOUT)
                    except Exception as exc:
                        await self._pool.close()
                        self._pool = None
                        raise DatabaseError(
                            f"could not connect to the database: {await self._probe_error()}"
                        ) from exc
                    logger.debug("postgres_pool_opened", dsn=self._config.resolved_dsn)
        return self._pool

    async def _probe_error(self) -> str:
        """Return the underlying connection error via one short direct attempt."""
        try:
            connection = await psycopg.AsyncConnection.connect(
                self._config.resolved_dsn, connect_timeout=5
            )
            await connection.close()
        except Exception as exc:  # noqa: BLE001 - the message is the point
            return str(exc).strip() or type(exc).__name__
        return "unknown connection error"

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        try:
            async with pool.connection() as connection, connection.cursor() as cursor:
                # psycopg only parses placeholders when params are bound.  Passing
                # None for empty parameter sets avoids conflicts with literal '%'
                # characters in SQL (e.g. LIKE patterns).
                await cursor.execute(sql, params or None)
                if cursor.description is None:
                    return []
                columns = [column.name for column in cursor.description]
                return [dict(zip(columns, row, strict=True)) for row in await cursor.fetchall()]
        except psycopg.Error as exc:
            raise DatabaseError(f"query failed: {exc}") from exc

    async def test_connection(self) -> None:
        await self.execute("SELECT 1 AS ok", {})

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.debug("postgres_pool_closed")
