"""MySQL adapter built on asyncmy.

Connections are pooled through :class:`asyncmy.pool.Pool`; each tool call
checks out a connection, executes the statement and returns rows as dicts.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any
from urllib.parse import unquote, urlsplit

import asyncmy
import structlog

from blueprint.config import DatabaseConfig
from blueprint.db.base import DatabaseAdapter
from blueprint.errors import DatabaseError

logger = structlog.get_logger(__name__)

_MYSQL_PORT = 3306
#: DatabaseConfig defaults the port to PostgreSQL's 5432; treat it as "unset"
#: for the MySQL adapter so a parts-based configuration still connects.
_PG_DEFAULT_PORT = 5432


class MySQLAdapter(DatabaseAdapter):
    """Async MySQL adapter using an :class:`asyncmy.pool.Pool`."""

    engine = "mysql"

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._pool: asyncmy.pool.Pool | None = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> asyncmy.pool.Pool:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    try:
                        self._pool = await asyncmy.pool.create_pool(
                            minsize=self._config.pool.min_size,
                            maxsize=self._config.pool.max_size,
                            pool_recycle=3600,
                            autocommit=True,
                            charset="utf8mb4",
                            **self._connection_kwargs(),
                        )
                    except Exception as exc:  # noqa: BLE001 - message is the point
                        self._pool = None
                        raise DatabaseError(f"could not connect to the database: {exc}") from exc
                    logger.debug("mysql_pool_opened", dsn=self._config.resolved_dsn)
        return self._pool

    def _connection_kwargs(self) -> dict[str, Any]:
        """Return asyncmy connection parameters from DSN or config parts."""
        dsn = os.environ.get("MCP_BLUEPRINT_DATABASE_URL") or self._config.dsn
        if dsn:
            parts = urlsplit(dsn)
            kwargs: dict[str, Any] = {
                "host": parts.hostname or "localhost",
                "port": parts.port or _MYSQL_PORT,
                "user": unquote(parts.username or "") if parts.username else "",
                "password": unquote(parts.password or "") if parts.password else "",
                "database": parts.path.lstrip("/") or None,
            }
            return kwargs
        port = self._config.port
        if port == _PG_DEFAULT_PORT:
            port = _MYSQL_PORT
        return {
            "host": self._config.host,
            "port": port,
            "user": self._config.user,
            "password": self._config.password,
            "database": self._config.dbname or None,
        }

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        pool = await self._get_pool()
        try:
            async with pool.acquire() as connection, connection.cursor() as cursor:
                # asyncmy only interpolates placeholders when params are bound.
                # Passing None for empty parameter sets avoids conflicts with
                # literal '%' characters in SQL (e.g. LIKE patterns).
                await cursor.execute(sql, params or None)
                if cursor.description is None:
                    return []
                columns = [column[0] for column in cursor.description]
                rows = await cursor.fetchall()
                return [dict(zip(columns, row, strict=True)) for row in rows]
        except asyncmy.errors.Error as exc:
            raise DatabaseError(f"query failed: {exc}") from exc

    async def test_connection(self) -> None:
        await self.execute("SELECT 1 AS ok", {})

    async def close(self) -> None:
        if self._pool is not None:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None
            logger.debug("mysql_pool_closed")
