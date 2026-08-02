"""Unit tests for the execution pipeline using a fake adapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from blueprint.cache import Cache
from blueprint.db.base import DatabaseAdapter
from blueprint.errors import (
    DatabaseError,
    ToolDisabledError,
    ToolNotFoundError,
    ToolValidationError,
)
from blueprint.formatting import ResultFormatter
from blueprint.pipeline import ToolPipeline
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer
from blueprint.tools.model import FormatConfig, ToolMetadata
from blueprint.tools.registry import ToolRegistry
from tests.conftest import FakeAdapter


def build_pipeline(
    adapter: DatabaseAdapter,
    metadata: ToolMetadata,
    rows: list[dict] | None = None,
    default_ttl: int | None = 30,
) -> ToolPipeline:
    registry = ToolRegistry()
    registry.register(metadata)
    return ToolPipeline(
        registry=registry,
        sql_loader=SQLLoader(),
        renderer=SQLRenderer(),
        adapter=adapter,
        formatter=ResultFormatter(),
        cache=Cache(),
        default_ttl=default_ttl,
    )


def make_metadata(tmp_path: Path, rows_ttl: int | None = None) -> ToolMetadata:
    sql_file = tmp_path / "data.sql"
    sql_file.write_text(
        "SELECT * FROM t\n{% if database %}\nWHERE datname = %(database)s\n{% endif %}\n",
        encoding="utf-8",
    )
    return ToolMetadata(
        name="get_data",
        description="Test tool.",
        parameters={
            "database": {"type": "string", "required": False, "default": None},
            "limit": {"type": "integer", "required": False, "default": 100},
        },
        sql=str(sql_file),
        source=str(tmp_path / "get_data.yaml"),
        cache={"ttl": rows_ttl} if rows_ttl is not None else None,
    )


async def test_pipeline_executes_and_returns_response(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"datname": "pgbench", "n": 1}])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    result = await pipeline.execute("get_data", {"database": "pgbench"})
    assert result["status"] == "success"
    assert result["row_count"] == 1
    assert result["cache_hit"] is False
    assert result["rows"] == [{"datname": "pgbench", "n": 1}]
    assert "duration_ms" in result


async def test_pipeline_renders_optional_filter(tmp_path) -> None:
    adapter = FakeAdapter(rows=[])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    await pipeline.execute("get_data", {"database": "pgbench"})
    sql, _ = adapter.executed[0]
    assert "WHERE datname = %(database)s" in sql

    adapter2 = FakeAdapter(rows=[])
    pipeline2 = build_pipeline(adapter2, make_metadata(tmp_path))
    await pipeline2.execute("get_data", {})
    sql2, _ = adapter2.executed[0]
    assert "WHERE" not in sql2


async def test_pipeline_cache_second_call(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"n": 1}])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path, rows_ttl=60))
    await pipeline.execute("get_data", {})
    assert len(adapter.executed) == 1
    result = await pipeline.execute("get_data", {})
    assert result["cache_hit"] is True
    assert len(adapter.executed) == 1


async def test_pipeline_no_cache_when_ttl_none(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"n": 1}])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path, rows_ttl=None), default_ttl=None)
    await pipeline.execute("get_data", {})
    await pipeline.execute("get_data", {})
    assert len(adapter.executed) == 2


async def test_unknown_tool(tmp_path) -> None:
    pipeline = build_pipeline(FakeAdapter(), make_metadata(tmp_path))
    with pytest.raises(ToolNotFoundError):
        await pipeline.execute("missing", {})


async def test_disabled_tool(tmp_path) -> None:
    metadata = make_metadata(tmp_path)
    metadata.enabled = False
    pipeline = build_pipeline(FakeAdapter(), metadata)
    with pytest.raises(ToolDisabledError):
        await pipeline.execute("get_data", {})


async def test_invalid_params(tmp_path) -> None:
    pipeline = build_pipeline(FakeAdapter(), make_metadata(tmp_path))
    with pytest.raises(ToolValidationError):
        await pipeline.execute("get_data", {"bogus": 1})


async def test_database_error_propagates(tmp_path) -> None:
    adapter = FakeAdapter(rows=[])
    adapter.fail = DatabaseError("boom")
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    with pytest.raises(DatabaseError, match="boom"):
        await pipeline.execute("get_data", {})


async def test_pipeline_applies_format(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"raw_size": 2048, "keep": True}])
    metadata = make_metadata(tmp_path)
    metadata.format = FormatConfig(rename={"raw_size": "size"}, convert_size=["size"])
    pipeline = build_pipeline(adapter, metadata)
    result = await pipeline.execute("get_data", {})
    assert result["rows"] == [{"size": "2.0 KB", "keep": True}]
