"""Integration tests for the pg-dba pack against a live PostgreSQL instance.

These tests are skipped when the database is not reachable.  The target
connection is taken from the ``MCP_BLUEPRINT_DATABASE_URL`` environment
variable or from the project ``config/database.yaml`` file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from blueprint.app import Blueprint
from blueprint.errors import DatabaseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOOLS = {
    "get_operational_kpis",
    "get_performance_kpis",
    "get_security_kpis",
    "get_users",
    "get_database_sizes",
    "get_database_version",
    "get_largest_objects",
    "get_replication_status",
    "get_tuning_configuration",
    "get_slow_queries",
    "get_maintenance_status",
    "get_index_health",
}


@pytest.fixture
async def blueprint() -> Blueprint:
    bp = Blueprint(config_path=str(PROJECT_ROOT / "config"))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"PostgreSQL not reachable: {exc}")
    bp.load_packs()
    yield bp
    await bp.close()


async def test_every_pack_tool_executes(blueprint: Blueprint) -> None:
    assert set(blueprint.list_tools()) >= EXPECTED_TOOLS
    pipeline = blueprint.pipeline
    for tool_name in EXPECTED_TOOLS:
        result = await pipeline.execute(tool_name, {})
        assert result["status"] == "success", tool_name
        assert "rows" in result
        assert result["row_count"] == len(result["rows"])


async def test_kpi_tools_return_status_rows(blueprint: Blueprint) -> None:
    kpi_columns = {"kpi_name", "current_value", "unit", "suggested_threshold", "status"}
    for tool_name in ("get_operational_kpis", "get_performance_kpis", "get_security_kpis"):
        result = await blueprint.pipeline.execute(tool_name, {})
        assert result["row_count"] > 0, tool_name
        for row in result["rows"]:
            assert set(row) == kpi_columns, tool_name
            assert row["status"] in {"ok", "warning", "error"}, tool_name


async def test_replication_tool_reports_instance(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_replication_status", {})
    components = {row["component"] for row in result["rows"]}
    assert "instance" in components


async def test_detail_tools_are_ordered_and_limited(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_largest_objects", {})
    sizes = [row["size_bytes"] for row in result["rows"]]
    assert sizes == sorted(sizes, reverse=True)
    assert len(result["rows"]) <= 32


async def test_largest_objects_parameter_filter(blueprint: Blueprint) -> None:
    unfiltered = await blueprint.pipeline.execute("get_largest_objects", {})
    assert unfiltered["row_count"] > 0
    prefix = unfiltered["rows"][0]["name"][:4]

    filtered = await blueprint.pipeline.execute(
        "get_largest_objects", {"object_name": f"{prefix}%"}
    )
    assert filtered["status"] == "success"
    assert filtered["row_count"] > 0
    assert all(row["name"].startswith(prefix) for row in filtered["rows"])
    assert filtered["row_count"] <= unfiltered["row_count"]


async def test_database_version_returns_three_columns(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_database_version", {})
    assert result["row_count"] == 1
    row = result["rows"][0]
    assert set(row) == {"version", "version_number", "full_version"}
    parts = row["version"].split(".")
    assert len(parts) >= 2 and all(p.isdigit() for p in parts)
    assert str(row["version_number"]).isdigit()
    assert row["version"] in row["full_version"]


async def test_stdlib_server_registers_tools(blueprint: Blueprint) -> None:
    from mcp.server.fastmcp import FastMCP

    server = blueprint.create_server()
    assert isinstance(server, FastMCP)
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == set(blueprint.list_tools())
