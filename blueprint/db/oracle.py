"""Oracle adapter built on the python-oracledb async connection pool.

Connections are pooled through :class:`oracledb.AsyncConnectionPool`; each
tool call acquires a connection, executes the statement and returns rows as
dicts.  Column names are normalized to lowercase because Oracle uppercases
unquoted aliases.  psycopg3-style named placeholders are translated to Oracle
``:name`` binds.
"""

from __future__ import annotations

import asyncio
import os
from time import perf_counter
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit

import structlog

from blueprint.config import DatabaseConfig
from blueprint.db.base import DatabaseAdapter
from blueprint.db.placeholders import to_oracle
from blueprint.errors import DatabaseError

if TYPE_CHECKING:
    from blueprint.metrics import Metrics

logger = structlog.get_logger(__name__)

_ORACLE_PORT = 1521
#: DatabaseConfig defaults the port to PostgreSQL's 5432; treat it as "unset"
#: for the Oracle adapter so a parts-based configuration still connects.
_PG_DEFAULT_PORT = 5432


class OracleAdapter(DatabaseAdapter):
    """Async Oracle adapter using an :class:`oracledb.AsyncConnectionPool`."""

    engine = "oracle"

    def __init__(self, config: DatabaseConfig, metrics: Metrics | None = None) -> None:
        self._config = config
        self._metrics = metrics
        self._pool: Any = None
        self._lock = asyncio.Lock()

    async def _get_pool(self) -> Any:
        if self._pool is None:
            async with self._lock:
                if self._pool is None:
                    try:
                        import oracledb
                    except ImportError as exc:  # pragma: no cover - optional extra
                        raise DatabaseError(
                            "oracledb is not installed; install the 'oracle' extra "
                            "(pip install 'mcp-blueprint[oracle]')"
                        ) from exc
                    try:
                        self._pool = oracledb.create_pool_async(
                            min=max(self._config.pool.min_size, 1),
                            max=max(self._config.pool.max_size, 1),
                            increment=1,
                            **self._connection_kwargs(),
                        )
                    except Exception as exc:  # noqa: BLE001 - message is the point
                        self._pool = None
                        raise DatabaseError(f"could not connect to the database: {exc}") from exc
                    logger.debug("oracle_pool_opened", dsn=self._config.resolved_dsn)
        return self._pool

    def _connection_kwargs(self) -> dict[str, Any]:
        """Return oracledb pool parameters from DSN or config parts."""
        dsn = os.environ.get("MCP_BLUEPRINT_DATABASE_URL") or self._config.dsn
        if dsn:
            parts = urlsplit(dsn)
            service = parts.path.lstrip("/") or None
            host = parts.hostname or "localhost"
            port = parts.port or _ORACLE_PORT
            kwargs: dict[str, Any] = {
                "user": unquote(parts.username or "") if parts.username else "",
                "password": unquote(parts.password or "") if parts.password else "",
            }
            if service:
                kwargs["dsn"] = f"{host}:{port}/{service}"
            else:
                kwargs["dsn"] = f"{host}:{port}"
            return kwargs
        port = self._config.port
        if port == _PG_DEFAULT_PORT:
            port = _ORACLE_PORT
        dsn = f"{self._config.host}:{port}"
        if self._config.dbname:
            dsn = f"{dsn}/{self._config.dbname}"
        return {
            "user": self._config.user,
            "password": self._config.password,
            "dsn": dsn,
        }

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started = perf_counter()
        pool: Any = None
        ok = False
        try:
            pool = await self._get_pool()
            async with pool.acquire() as connection:
                with connection.cursor() as cursor:
                    await cursor.execute(to_oracle(sql), params)
                    if cursor.description is None:
                        return []
                    columns = [column[0].lower() for column in cursor.description]
                    rows = await cursor.fetchall()
                    result = [dict(zip(columns, row, strict=True)) for row in rows]
                    ok = True
                    return result
        except Exception as exc:  # noqa: BLE001 - message is the point
            raise DatabaseError(f"query failed: {exc}") from exc
        finally:
            if self._metrics is not None:
                self._metrics.record_db_query(
                    self.engine, perf_counter() - started, error=not ok
                )

    async def test_connection(self) -> None:
        await self.execute("SELECT 1 AS ok FROM dual", {})

    async def close(self) -> None:
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.debug("oracle_pool_closed")
