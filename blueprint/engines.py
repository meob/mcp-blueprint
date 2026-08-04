"""Supported database engine identifiers.

Engine names are canonical (``postgresql``, ``mysql``, ``oracle``) and are used
both in configuration and in tool metadata.  Legacy aliases map to the
canonical name.
"""

from __future__ import annotations

SUPPORTED_ENGINES: frozenset[str] = frozenset(
    {
        "postgresql",
        "mysql",
        "oracle",
        "clickhouse",
        "sqlserver",
        "mariadb",
    }
)

ENGINE_ALIASES: dict[str, str] = {
    "postgres": "postgresql",
    "mssql": "sqlserver",
    "sql_server": "sqlserver",
}


def canonical_engine(engine: str) -> str:
    """Return the canonical name for ``engine``."""
    return ENGINE_ALIASES.get(engine, engine)
