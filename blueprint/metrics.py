"""Prometheus metrics.

Instrumentation is optional: an instance of :class:`Metrics` is created only
when ``metrics.enabled`` is true, and every component receives ``None``
otherwise.  The module is importable without ``prometheus-client``; the
library is required only at construction time, so frameworks that do not
enable metrics never pay for the dependency.

Metric naming follows Prometheus conventions: counters end in ``_total``,
histograms carry a ``_seconds`` unit suffix, and every metric is namespaced
with ``blueprint_``.  Label cardinality is bounded (tool, pack, status,
engine), never per-request values.

The default registry is used when none is injected, which also serves the
standard ``process_*`` and ``python_info`` metrics.
"""

from __future__ import annotations

from typing import Any, cast

from blueprint.config import MetricsConfig
from blueprint.errors import ConfigurationError

try:
    from prometheus_client import REGISTRY as _REGISTRY
    from prometheus_client import (
        Counter as _Counter,
    )
    from prometheus_client import (
        Gauge as _Gauge,
    )
    from prometheus_client import (
        Histogram as _Histogram,
    )
    from prometheus_client import (
        start_http_server,
    )
except ImportError:
    _REGISTRY = cast(Any, None)
    _Counter = cast(Any, None)  # type: ignore[misc]
    _Gauge = cast(Any, None)  # type: ignore[misc]
    _Histogram = cast(Any, None)  # type: ignore[misc]
    start_http_server = cast(Any, None)


def _require_prometheus() -> None:
    """Raise a clear error when prometheus-client is not installed."""
    if _Counter is None:
        raise ConfigurationError(
            "metrics are enabled but 'prometheus-client' is not installed; "
            "install it with 'pip install mcp-blueprint[metrics]'"
        )


class Metrics:
    """Holds every framework metric and provides recording helpers.

    The class keeps the metric definitions in one place so components only
    call small helpers instead of reaching into the registry.
    """

    _BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    _ROW_BUCKETS = (0, 1, 5, 10, 50, 100, 500, 1000, 5000, float("inf"))

    def __init__(self, registry: Any | None = None) -> None:
        _require_prometheus()
        if _REGISTRY is None:  # pragma: no cover - guarded by _require_prometheus
            raise ConfigurationError("prometheus-client is not available")
        self._registry = registry or _REGISTRY
        counter = cast(Any, _Counter)
        gauge = cast(Any, _Gauge)
        histogram = cast(Any, _Histogram)

        def mk(metric_type: str, name: str, doc: str, labels: list[str]) -> Any:
            builder = {"counter": counter, "gauge": gauge, "histogram": histogram}[metric_type]
            return builder(name, doc, labels, registry=self._registry)

        self.tool_calls = mk(
            "counter",
            "blueprint_tool_calls_total",
            "Tool invocations by status.",
            ["tool", "pack", "status"],
        )
        self.tool_duration = histogram(
            "blueprint_tool_duration_seconds",
            "Tool execution latency in seconds.",
            ["tool", "pack"],
            buckets=self._BUCKETS,
            registry=self._registry,
        )
        self.tool_rows = histogram(
            "blueprint_tool_rows",
            "Rows returned per tool call.",
            ["tool"],
            buckets=self._ROW_BUCKETS,
            registry=self._registry,
        )
        self.tool_cache_hits = mk(
            "counter", "blueprint_tool_cache_hits_total", "Cache hits per tool.", ["tool"]
        )
        self.tool_cache_misses = mk(
            "counter", "blueprint_tool_cache_misses_total", "Cache misses per tool.", ["tool"]
        )

        self.cache_entries = mk(
            "gauge", "blueprint_cache_entries", "Current number of cached entries.", []
        )
        self.cache_maxsize = mk(
            "gauge", "blueprint_cache_maxsize", "Configured cache max size per TTL bucket.", []
        )

        self.db_queries = mk(
            "counter", "blueprint_db_queries_total", "Database queries executed.", ["engine"]
        )
        self.db_query_duration = histogram(
            "blueprint_db_query_duration_seconds",
            "Database query latency in seconds.",
            ["engine"],
            buckets=self._BUCKETS,
            registry=self._registry,
        )
        self.db_errors = mk(
            "counter", "blueprint_db_errors_total", "Database queries that failed.", ["engine"]
        )
        self.db_pool_size = mk(
            "gauge", "blueprint_db_pool_size", "Current open pool connections.", ["engine"]
        )
        self.db_pool_idle = mk(
            "gauge", "blueprint_db_pool_idle", "Current idle pool connections.", ["engine"]
        )
        self.db_pool_max = mk("gauge", "blueprint_db_pool_max", "Maximum pool size.", ["engine"])
        self.db_pool_waiting = mk(
            "gauge", "blueprint_db_pool_waiting", "Queries waiting for a connection.", ["engine"]
        )

        self.tools_registered = mk(
            "gauge", "blueprint_tools_registered", "Number of registered tools.", []
        )
        self.packs_loaded = mk("gauge", "blueprint_packs_loaded", "Number of loaded packs.", [])

    @property
    def registry(self) -> Any:
        """Return the underlying collector registry."""
        return self._registry

    def render(self) -> bytes:
        """Return the Prometheus text exposition of the collected metrics."""
        from prometheus_client import generate_latest

        return generate_latest(self._registry)

    def record_success(self, tool: str, pack: str, duration_ms: float, rows: int) -> None:
        """Record a successful tool execution."""
        self.tool_calls.labels(tool, pack, "success").inc()
        self.tool_duration.labels(tool, pack).observe(duration_ms / 1000.0)
        self.tool_rows.labels(tool).observe(rows)

    def record_error(self, tool: str, pack: str, duration_ms: float) -> None:
        """Record a failed tool execution (including validation rejections)."""
        self.tool_calls.labels(tool, pack, "error").inc()
        self.tool_duration.labels(tool, pack).observe(duration_ms / 1000.0)

    def record_cache(self, tool: str, hit: bool) -> None:
        """Record a cache hit or miss for a tool."""
        if hit:
            self.tool_cache_hits.labels(tool).inc()
        else:
            self.tool_cache_misses.labels(tool).inc()

    def set_cache_stats(self, entries: int, maxsize: int) -> None:
        """Refresh the cache size gauges."""
        self.cache_entries.set(entries)
        self.cache_maxsize.set(maxsize)

    def record_db_query(self, engine: str, duration_seconds: float, error: bool) -> None:
        """Record a database query, its duration and, on failure, an error."""
        self.db_queries.labels(engine).inc()
        self.db_query_duration.labels(engine).observe(duration_seconds)
        if error:
            self.db_errors.labels(engine).inc()

    def set_pool_stats(
        self,
        engine: str,
        size: int | None = None,
        idle: int | None = None,
        max_size: int | None = None,
        waiting: int | None = None,
    ) -> None:
        """Refresh the pool gauges; only the provided values are updated."""
        if size is not None:
            self.db_pool_size.labels(engine).set(size)
        if idle is not None:
            self.db_pool_idle.labels(engine).set(idle)
        if max_size is not None:
            self.db_pool_max.labels(engine).set(max_size)
        if waiting is not None:
            self.db_pool_waiting.labels(engine).set(waiting)

    def set_server_stats(self, tools: int, packs: int) -> None:
        """Refresh the server gauges after pack loading."""
        self.tools_registered.set(tools)
        self.packs_loaded.set(packs)


def start_metrics_server(config: MetricsConfig) -> None:
    """Start the Prometheus HTTP endpoint in a background thread.

    The endpoint serves the default registry on ``host:port/metrics`` and
    works regardless of the MCP transport, including stdio.
    """
    if not config.enabled:
        return
    _require_prometheus()
    start_http_server(config.port, addr=config.host)
