"""SQL Server adapter built on pyodbc.

pyodbc is synchronous, so queries and connection setup run in worker threads
through :func:`asyncio.to_thread`.  A small async pool keeps a bounded set of
open connections.  psycopg3-style named placeholders are translated to ODBC
positional ``?`` markers.
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
from blueprint.db.placeholders import to_pyodbc
from blueprint.errors import DatabaseError

if TYPE_CHECKING:
    from blueprint.metrics import Metrics

logger = structlog.get_logger(__name__)

_SQLSERVER_PORT = 1433
#: DatabaseConfig defaults the port to PostgreSQL's 5432; treat it as "unset"
#: for the SQL Server adapter so a parts-based configuration still connects.
_PG_DEFAULT_PORT = 5432

_CONNECT_TIMEOUT = 10


class SQLServerAdapter(DatabaseAdapter):
    """Async SQL Server adapter running pyodbc in worker threads."""

    engine = "sqlserver"

    def __init__(self, config: DatabaseConfig, metrics: Metrics | None = None) -> None:
        self._config = config
        self._metrics = metrics
        self._queue: asyncio.Queue[Any] | None = None
        self._created = 0
        self._lock = asyncio.Lock()

    def _connection_kwargs(self) -> dict[str, str]:
        """Return host, port, database, user and password from DSN or parts."""
        dsn = os.environ.get("MCP_BLUEPRINT_DATABASE_URL") or self._config.dsn
        if dsn:
            parts = urlsplit(dsn)
            return {
                "host": parts.hostname or "localhost",
                "port": str(parts.port or _SQLSERVER_PORT),
                "database": parts.path.lstrip("/"),
                "user": unquote(parts.username or "") if parts.username else "",
                "password": unquote(parts.password or "") if parts.password else "",
            }
        port = self._config.port
        if port == _PG_DEFAULT_PORT:
            port = _SQLSERVER_PORT
        return {
            "host": self._config.host,
            "port": str(port),
            "database": self._config.dbname,
            "user": self._config.user,
            "password": self._config.password,
        }

    def _connection_string(self) -> str:
        kwargs = self._connection_kwargs()
        return (
            "DRIVER={ODBC Driver 18 for SQL Server};"
            f"SERVER={kwargs['host']},{kwargs['port']};"
            f"DATABASE={kwargs['database']};"
            f"UID={kwargs['user']};"
            f"PWD={kwargs['password']};"
            "Encrypt=optional;TrustServerCertificate=yes;"
        )

    def _create_connection(self) -> Any:
        try:
            import pyodbc
        except ImportError as exc:  # pragma: no cover - optional extra
            raise DatabaseError(
                "pyodbc is not installed; install the 'sqlserver' extra "
                "(pip install 'mcp-blueprint[sqlserver]')"
            ) from exc
        try:
            return pyodbc.connect(
                self._connection_string(), timeout=_CONNECT_TIMEOUT, autocommit=True
            )
        except Exception as exc:  # noqa: BLE001 - message is the point
            raise DatabaseError(f"could not connect to the database: {exc}") from exc

    async def _acquire(self) -> Any:
        if self._queue is None:
            async with self._lock:
                if self._queue is None:
                    self._queue = asyncio.Queue(maxsize=max(self._config.pool.max_size, 1))
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            async with self._lock:
                create = self._created < max(self._config.pool.max_size, 1)
                if create:
                    self._created += 1
            if create:
                try:
                    return await asyncio.to_thread(self._create_connection)
                except Exception:
                    self._created -= 1
                    raise
            return await self._queue.get()

    def _run_query(self, connection: Any, sql: str, values: list[Any]) -> list[dict[str, Any]]:
        cursor = connection.cursor()
        try:
            cursor.execute(sql, values)
            if cursor.description is None:
                return []
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row, strict=True)) for row in rows]
        finally:
            cursor.close()

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started = perf_counter()
        connection: Any = None
        ok = False
        try:
            connection = await self._acquire()
            translated, values = to_pyodbc(sql, params)
            result = await asyncio.to_thread(self._run_query, connection, translated, values)
            ok = True
            return result
        except DatabaseError:
            raise
        except Exception as exc:  # noqa: BLE001 - message is the point
            raise DatabaseError(f"query failed: {exc}") from exc
        finally:
            if connection is not None:
                self._queue.put_nowait(connection)
            if self._metrics is not None:
                self._metrics.record_db_query(
                    self.engine, perf_counter() - started, error=not ok
                )

    async def test_connection(self) -> None:
        await self.execute("SELECT 1 AS ok", {})

    async def close(self) -> None:
        if self._queue is not None:
            while not self._queue.empty():
                try:
                    connection = self._queue.get_nowait()
                    await asyncio.to_thread(connection.close)
                except Exception:  # noqa: BLE001 - best effort close
                    pass
            self._queue = None
            self._created = 0
            logger.debug("sqlserver_pool_closed")
