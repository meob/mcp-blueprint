"""Execution pipeline.

Each tool call flows through the same stages: metadata lookup, parameter
validation, cache lookup, SQL loading and rendering, database execution,
result formatting and finally JSON-safe serialization.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import structlog

from blueprint.cache import Cache
from blueprint.db.base import DatabaseAdapter
from blueprint.errors import ToolSecurityError
from blueprint.formatting import ResultFormatter, json_safe
from blueprint.sql.guard import ensure_read_only, ensure_single_statement
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer
from blueprint.tools.registry import ToolRegistry
from blueprint.validation import validate_parameters

logger = structlog.get_logger(__name__)


class ToolPipeline:
    """Orchestrates a single tool execution."""

    def __init__(
        self,
        registry: ToolRegistry,
        sql_loader: SQLLoader,
        renderer: SQLRenderer,
        adapter: DatabaseAdapter,
        formatter: ResultFormatter,
        cache: Cache,
        default_ttl: int | None = 30,
        max_rows: int | None = None,
    ) -> None:
        self._registry = registry
        self._sql_loader = sql_loader
        self._renderer = renderer
        self._adapter = adapter
        self._formatter = formatter
        self._cache = cache
        self._default_ttl = default_ttl
        self._max_rows = max_rows

    async def execute(self, tool_name: str, raw_params: dict[str, Any]) -> dict[str, Any]:
        """Run the tool named ``tool_name`` and return a JSON-safe response."""
        started = perf_counter()
        metadata = self._registry.get(tool_name)
        if not metadata.enabled:
            from blueprint.errors import ToolDisabledError

            raise ToolDisabledError(f"tool is disabled: {tool_name}")

        sql_path = metadata.sql_for(self._adapter.engine)
        if sql_path is None:
            from blueprint.errors import ToolNotFoundError

            raise ToolNotFoundError(
                f"tool is not available for engine {self._adapter.engine}: {tool_name}"
            )

        params = validate_parameters(metadata, raw_params)
        cache_key = (metadata.name, tuple(sorted(params.items())))

        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.info("tool_cache_hit", tool=tool_name)
            return self._response(metadata.name, cached, started, cache_hit=True)

        sql = self._sql_loader.load(sql_path, metadata.source)
        sql = self._renderer.render(sql, params)
        logger.debug("tool_executing", tool=tool_name, sql=sql)

        self._enforce_sql_policy(tool_name, sql, metadata.writes)

        bound = {name: value for name, value in params.items() if value is not None}
        rows = await self._adapter.execute(sql, bound)
        rows = self._formatter.apply(rows, metadata.format)
        rows = self._cap_rows(tool_name, rows)

        ttl = metadata.cache.ttl if metadata.cache else self._default_ttl
        if ttl:
            self._cache.set(cache_key, rows, ttl)

        return self._response(metadata.name, rows, started)

    def _enforce_sql_policy(self, tool_name: str, sql: str, writes: bool) -> None:
        """Reject rendered SQL that violates the read-only policy.

        Runs on the rendered statement, so it cannot be bypassed by template
        tricks: a parameter value can never change the statement because
        values are only ever bound, never interpolated.
        """
        try:
            if writes:
                ensure_single_statement(sql)
            else:
                ensure_read_only(sql)
        except ToolSecurityError as exc:
            raise ToolSecurityError(f"tool '{tool_name}' blocked: {exc}") from exc

    def _cap_rows(self, tool_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Bound the response size regardless of the query's own LIMIT."""
        if self._max_rows is None or len(rows) <= self._max_rows:
            return rows
        logger.warning(
            "rows_truncated",
            tool=tool_name,
            total=len(rows),
            max_rows=self._max_rows,
        )
        return rows[: self._max_rows]

    @staticmethod
    def _response(
        tool_name: str,
        rows: list[dict[str, Any]],
        started: float,
        cache_hit: bool = False,
    ) -> dict[str, Any]:
        safe_rows = [json_safe(row) for row in rows]
        return {
            "tool": tool_name,
            "status": "success",
            "row_count": len(safe_rows),
            "duration_ms": round((perf_counter() - started) * 1000, 2),
            "cache_hit": cache_hit,
            "rows": safe_rows,
        }
