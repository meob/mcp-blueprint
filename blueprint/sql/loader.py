"""Loading SQL statements from external files."""

from __future__ import annotations

from pathlib import Path

import structlog

from blueprint.errors import SQLLoadError

logger = structlog.get_logger(__name__)


class SQLLoader:
    """Loads SQL files, caching their content by absolute path.

    Relative paths are resolved against the tool definition file location, so
    a tool with ``source: /packs/pg-dba/tools/get_users.yaml`` and
    ``sql: ../sql/get_users.sql`` loads
    ``/packs/pg-dba/sql/get_users.sql``.
    """

    def __init__(self) -> None:
        self._cache: dict[str, str] = {}

    def load(self, path: str, tool_source: str = "") -> str:
        """Return the SQL text for the given path.

        Absolute paths are used as-is.  Relative paths are resolved against the
        directory containing the tool definition file.
        """
        resolved = Path(path)
        if not resolved.is_absolute() and tool_source:
            resolved = Path(tool_source).parent / resolved
        key = str(resolved)
        if key in self._cache:
            return self._cache[key]
        try:
            content = resolved.read_text(encoding="utf-8")
        except OSError as exc:
            raise SQLLoadError(f"cannot read SQL file {resolved}: {exc}") from exc
        self._cache[key] = content
        logger.debug("loaded_sql", sql=key)
        return content
