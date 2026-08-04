"""ClickHouse adapter built on the clickhouse-driver synchronous client.

clickhouse-driver removed its native asyncio client (``clickhouse_driver.aio``)
after version 0.2.6, so the synchronous :class:`clickhouse_driver.Client` is
wrapped in ``asyncio.to_thread``.  Python-style named placeholders
(``%(name)s``) are substituted client-side; literal ``%`` characters must be
escaped as ``%%`` in tool SQL.
"""

from __future__ import annotations

import asyncio
import os
from contextlib import suppress
from time import perf_counter
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlsplit

import structlog

from blueprint.config import DatabaseConfig
from blueprint.db.base import DatabaseAdapter
from blueprint.errors import DatabaseError

if TYPE_CHECKING:
    from blueprint.metrics import Metrics

logger = structlog.get_logger(__name__)

_CLICKHOUSE_PORT = 9000
#: DatabaseConfig defaults the port to PostgreSQL's 5432; treat it as "unset"
#: for the ClickHouse adapter so a parts-based configuration still connects.
_PG_DEFAULT_PORT = 5432


class ClickHouseAdapter(DatabaseAdapter):
    """ClickHouse adapter using a shared :class:`clickhouse_driver.Client`."""

    engine = "clickhouse"

    def __init__(self, config: DatabaseConfig, metrics: Metrics | None = None) -> None:
        self._config = config
        self._metrics = metrics
        self._client: Any = None
        self._lock = asyncio.Lock()

    async def _get_client(self) -> Any:
        if self._client is None:
            async with self._lock:
                if self._client is None:
                    try:
                        from clickhouse_driver import Client
                    except ImportError as exc:  # pragma: no cover - optional extra
                        raise DatabaseError(
                            "clickhouse-driver is not installed; install the 'clickhouse' "
                            "extra (pip install 'mcp-blueprint[clickhouse]')"
                        ) from exc
                    try:
                        self._client = Client(
                            **self._connection_kwargs(),
                            settings={"readonly": 1},
                        )
                    except Exception as exc:  # noqa: BLE001 - message is the point
                        self._client = None
                        raise DatabaseError(f"could not connect to the database: {exc}") from exc
                    logger.debug("clickhouse_client_opened", dsn=self._config.resolved_dsn)
        return self._client

    def _connection_kwargs(self) -> dict[str, Any]:
        """Return clickhouse-driver connection parameters from DSN or parts."""
        dsn = os.environ.get("MCP_BLUEPRINT_DATABASE_URL") or self._config.dsn
        if dsn:
            parts = urlsplit(dsn)
            return {
                "host": parts.hostname or "localhost",
                "port": parts.port or _CLICKHOUSE_PORT,
                "user": unquote(parts.username or "") if parts.username else "",
                "password": unquote(parts.password or "") if parts.password else "",
                "database": parts.path.lstrip("/") or "default",
            }
        port = self._config.port
        if port == _PG_DEFAULT_PORT:
            port = _CLICKHOUSE_PORT
        return {
            "host": self._config.host,
            "port": port,
            "user": self._config.user,
            "password": self._config.password,
            "database": self._config.dbname or "default",
        }

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        started = perf_counter()
        ok = False
        try:
            client = await self._get_client()
            # clickhouse-driver only interprets placeholders when params are
            # bound; None avoids conflicts with literal '%' characters.
            rows, columns = await asyncio.to_thread(
                client.execute, sql, params or None, with_column_types=True
            )
            names = [column[0] for column in columns]
            result = [dict(zip(names, row, strict=True)) for row in rows]
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
        await self.execute("SELECT 1 AS ok", {})

    async def close(self) -> None:
        if self._client is not None:
            with suppress(Exception):
                await asyncio.to_thread(self._client.disconnect)
            self._client = None
            logger.debug("clickhouse_client_closed")
