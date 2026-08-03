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
    ToolSecurityError,
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
    max_rows: int | None = None,
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
        max_rows=max_rows,
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


async def test_pipeline_binds_only_non_none_params(tmp_path) -> None:
    adapter = FakeAdapter(rows=[])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    await pipeline.execute("get_data", {})
    _, params = adapter.executed[0]
    assert params == {"limit": 100}

    adapter2 = FakeAdapter(rows=[])
    pipeline2 = build_pipeline(adapter2, make_metadata(tmp_path))
    await pipeline2.execute("get_data", {"database": "pgbench"})
    _, params2 = adapter2.executed[0]
    assert params2 == {"database": "pgbench", "limit": 100}


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


def make_write_metadata(tmp_path: Path, sql_text: str) -> ToolMetadata:
    sql_file = tmp_path / "write.sql"
    sql_file.write_text(sql_text, encoding="utf-8")
    return ToolMetadata(
        name="mutate_data",
        description="Write tool.",
        sql=str(sql_file),
        source=str(tmp_path / "mutate_data.yaml"),
    )


async def test_pipeline_blocks_non_read_only_sql(tmp_path) -> None:
    adapter = FakeAdapter()
    metadata = make_write_metadata(tmp_path, "UPDATE t SET name = %(name)s")
    pipeline = build_pipeline(adapter, metadata)
    with pytest.raises(ToolSecurityError, match="not read-only"):
        await pipeline.execute("mutate_data", {})
    assert adapter.executed == []


async def test_pipeline_allows_write_when_declared(tmp_path) -> None:
    adapter = FakeAdapter(rows=[])
    metadata = make_write_metadata(tmp_path, "UPDATE t SET name = %(name)s")
    metadata.writes = True
    pipeline = build_pipeline(adapter, metadata)
    result = await pipeline.execute("mutate_data", {})
    assert result["status"] == "success"
    assert adapter.executed[0][0].startswith("UPDATE")


async def test_pipeline_blocks_stacked_statements(tmp_path) -> None:
    adapter = FakeAdapter()
    metadata = make_write_metadata(tmp_path, "SELECT 1; DROP TABLE t")
    metadata.writes = True
    pipeline = build_pipeline(adapter, metadata)
    with pytest.raises(ToolSecurityError, match="exactly one statement"):
        await pipeline.execute("mutate_data", {})
    assert adapter.executed == []


async def test_pipeline_caps_rows(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"n": i} for i in range(5)])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path), max_rows=3)
    result = await pipeline.execute("get_data", {})
    assert result["row_count"] == 3
    assert len(result["rows"]) == 3


async def test_pipeline_no_cap_when_configured_none(tmp_path) -> None:
    adapter = FakeAdapter(rows=[{"n": i} for i in range(5)])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path), max_rows=None)
    result = await pipeline.execute("get_data", {})
    assert result["row_count"] == 5


async def test_pipeline_emits_audit_record(tmp_path) -> None:
    import json

    from blueprint.config import AuditConfig, LoggingConfig
    from blueprint.logging import configure_logging

    audit_file = tmp_path / "audit.jsonl"
    configure_logging(LoggingConfig(audit=AuditConfig(enabled=True, file_path=str(audit_file))))
    adapter = FakeAdapter(rows=[{"datname": "pgbench", "n": 1}])
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    result = await pipeline.execute("get_data", {"database": "pgbench"})
    assert result["status"] == "success"

    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "tool_executed"
    assert record["tool"] == "get_data"
    assert record["status"] == "success"
    assert record["rows"] == 1
    assert record["cache_hit"] is False
    assert record["trace_id"]


async def test_pipeline_emits_audit_record_on_error(tmp_path) -> None:
    import json

    from blueprint.config import AuditConfig, LoggingConfig
    from blueprint.logging import configure_logging

    audit_file = tmp_path / "audit.jsonl"
    configure_logging(LoggingConfig(audit=AuditConfig(enabled=True, file_path=str(audit_file))))
    adapter = FakeAdapter(rows=[])
    adapter.fail = DatabaseError("boom")
    pipeline = build_pipeline(adapter, make_metadata(tmp_path))
    with pytest.raises(DatabaseError):
        await pipeline.execute("get_data", {})

    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "tool_failed"
    assert record["tool"] == "get_data"
    assert record["status"] == "error"
    assert record["error"] == "boom"
    assert record["trace_id"]
