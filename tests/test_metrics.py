"""Unit tests for Prometheus metrics instrumentation."""

from __future__ import annotations

from pathlib import Path

import pytest
from prometheus_client import CollectorRegistry

from blueprint import server as server_module
from blueprint.app import Blueprint
from blueprint.cache import Cache
from blueprint.config import BlueprintConfig, MetricsConfig, load_config
from blueprint.errors import ToolValidationError
from blueprint.formatting import ResultFormatter
from blueprint.metrics import Metrics, start_metrics_server
from blueprint.pipeline import ToolPipeline
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer
from blueprint.tools.model import ToolMetadata
from blueprint.tools.registry import ToolRegistry
from tests.conftest import FakeAdapter


def make_metadata(tmp_path: Path) -> ToolMetadata:
    (tmp_path / "data.sql").write_text("SELECT 1", encoding="utf-8")
    return ToolMetadata(
        name="get_data",
        description="Test tool.",
        parameters={
            "database": {"type": "string", "required": False, "default": None},
            "limit": {"type": "integer", "required": False, "default": 10},
        },
        sql=str(tmp_path / "data.sql"),
        pack_name="test-pack",
        source=str(tmp_path / "get_data.yaml"),
    )


def build_pipeline(
    registry: ToolRegistry, metrics: Metrics | None = None, rows: list[dict] | None = None
) -> ToolPipeline:
    return ToolPipeline(
        registry=registry,
        sql_loader=SQLLoader(),
        renderer=SQLRenderer(),
        adapter=FakeAdapter(rows=rows or [{"value": 42}]),
        formatter=ResultFormatter(),
        cache=Cache(maxsize=8, metrics=metrics),
        metrics=metrics,
    )


def test_metrics_disabled_by_default() -> None:
    assert MetricsConfig().enabled is False
    assert BlueprintConfig().metrics.enabled is False


def test_load_config_reads_metrics_section(tmp_path) -> None:
    (tmp_path / "server.yaml").write_text("server:\n  name: my-server\n", encoding="utf-8")
    (tmp_path / "metrics.yaml").write_text(
        "metrics:\n  enabled: true\n  port: 9200\n", encoding="utf-8"
    )
    config = load_config(tmp_path)
    assert config.metrics.enabled is True
    assert config.metrics.port == 9200
    assert config.metrics.host == "127.0.0.1"


def test_render_contains_catalog(tmp_path) -> None:
    metrics = Metrics(CollectorRegistry())
    text = metrics.render().decode()
    expected = [
        "blueprint_tool_calls_total",
        "blueprint_tool_duration_seconds",
        "blueprint_tool_rows",
        "blueprint_tool_cache_hits_total",
        "blueprint_tool_cache_misses_total",
        "blueprint_cache_entries",
        "blueprint_cache_maxsize",
        "blueprint_db_queries_total",
        "blueprint_db_query_duration_seconds",
        "blueprint_db_errors_total",
        "blueprint_db_pool_size",
        "blueprint_db_pool_idle",
        "blueprint_db_pool_max",
        "blueprint_db_pool_waiting",
        "blueprint_tools_registered",
        "blueprint_packs_loaded",
    ]
    for name in expected:
        assert name in text, f"missing metric {name}"


async def test_pipeline_records_tool_metrics(tmp_path) -> None:
    metrics = Metrics(CollectorRegistry())
    registry = ToolRegistry()
    registry.register(make_metadata(tmp_path))
    pipeline = build_pipeline(registry, metrics=metrics)

    result = await pipeline.execute("get_data", {"limit": 5})
    await pipeline.execute("get_data", {"limit": 5})

    assert result["row_count"] == 1
    assert metrics.registry.get_sample_value(
        "blueprint_tool_calls_total",
        {"pack": "test-pack", "status": "success", "tool": "get_data"},
    ) == 2.0
    assert metrics.registry.get_sample_value(
        "blueprint_tool_cache_hits_total", {"tool": "get_data"}
    ) == 1.0
    assert metrics.registry.get_sample_value(
        "blueprint_tool_cache_misses_total", {"tool": "get_data"}
    ) == 1.0


async def test_pipeline_records_errors(tmp_path) -> None:
    metrics = Metrics(CollectorRegistry())
    registry = ToolRegistry()
    metadata = make_metadata(tmp_path)
    metadata.parameters["limit"].required = True
    registry.register(metadata)
    pipeline = build_pipeline(registry, metrics=metrics)

    with pytest.raises(ToolValidationError):
        await pipeline.execute("get_data", {})

    assert metrics.registry.get_sample_value(
        "blueprint_tool_calls_total",
        {"pack": "test-pack", "status": "error", "tool": "get_data"},
    ) == 1.0
    assert metrics.registry.get_sample_value(
        "blueprint_tool_calls_total",
        {"pack": "test-pack", "status": "success", "tool": "get_data"},
    ) is None


async def test_validation_gate_records_rejection(tmp_path) -> None:
    metrics = Metrics(CollectorRegistry())
    registry = ToolRegistry()
    registry.register(make_metadata(tmp_path))
    mcp = server_module.create_server(build_pipeline(registry), registry, "test", metrics=metrics)

    with pytest.raises(ToolValidationError):
        await mcp.call_tool("get_data", {"limit": "oops"})

    assert metrics.registry.get_sample_value(
        "blueprint_tool_calls_total",
        {"pack": "test-pack", "status": "error", "tool": "get_data"},
    ) == 1.0


def test_start_metrics_server_requires_enabled() -> None:
    start_metrics_server(MetricsConfig(enabled=False))
    start_metrics_server(MetricsConfig(enabled=True, port=0))


def test_blueprint_creates_metrics_only_when_enabled(tmp_path) -> None:
    blueprint = Blueprint(config=BlueprintConfig())
    assert blueprint.metrics is None

    enabled = BlueprintConfig(metrics=MetricsConfig(enabled=True))
    blueprint = Blueprint(config=enabled)
    assert blueprint.metrics is not None
