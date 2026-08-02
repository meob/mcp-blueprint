"""Database adapter interface and factory.

The framework never depends on a specific database engine.  Each engine
implements :class:`DatabaseAdapter`; only SQL and the adapter change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from blueprint.config import DatabaseConfig
from blueprint.errors import AdapterNotFoundError


class DatabaseAdapter(ABC):
    """Common interface implemented by every database engine adapter."""

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


def create_adapter(config: DatabaseConfig) -> DatabaseAdapter:
    """Create the adapter matching ``config.engine``."""
    if config.engine in {"postgresql", "postgres"}:
        from blueprint.db.postgres import PostgresAdapter

        return PostgresAdapter(config)
    raise AdapterNotFoundError(f"no adapter for engine: {config.engine}")
