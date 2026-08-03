"""Database adapter interface and factory.

The framework never depends on a specific database engine.  Each engine
implements :class:`DatabaseAdapter`; only SQL and the adapter change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from blueprint.config import DatabaseConfig
from blueprint.errors import AdapterNotFoundError

if TYPE_CHECKING:
    from blueprint.metrics import Metrics


class DatabaseAdapter(ABC):
    """Common interface implemented by every database engine adapter."""

    engine: str = ""
    """Canonical engine identifier (e.g. ``postgresql``)."""

    @abstractmethod
    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Execute ``sql`` with ``params`` and return rows as dicts.

        Parameters use psycopg3 named style (``%(name)s``).
        """

    @abstractmethod
    async def test_connection(self) -> None:
        """Verify the database is reachable, raising on failure."""

    @abstractmethod
    async def close(self) -> None:
        """Release all resources held by the adapter."""

    async def __aenter__(self) -> DatabaseAdapter:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()


def create_adapter(config: DatabaseConfig, metrics: Metrics | None = None) -> DatabaseAdapter:
    """Create the adapter matching ``config.engine``."""
    engine = config.engine_id
    if engine == "postgresql":
        from blueprint.db.postgres import PostgresAdapter

        return PostgresAdapter(config, metrics=metrics)
    if engine == "mysql":
        from blueprint.db.mysql import MySQLAdapter

        return MySQLAdapter(config, metrics=metrics)
    raise AdapterNotFoundError(f"no adapter for engine: {config.engine}")
