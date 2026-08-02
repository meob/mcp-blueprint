"""Integration tests for the dba pack against a live MySQL instance.

These tests are skipped when MySQL is not reachable.  The connection is taken
from the ``MCP_BLUEPRINT_MYSQL_URL`` environment variable and falls back to a
local ``monitor`` user on the ``mysakila`` database.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from blueprint.app import Blueprint
from blueprint.config import BlueprintConfig, DatabaseConfig, LoggingConfig, ServerConfig
from blueprint.errors import DatabaseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TOOLS = {
    "get_operational_kpis",
    "get_performance_kpis",
    "get_security_kpis",
    "get_users",
    "get_database_sizes",
    "get_largest_objects",
    "get_replication_status",
    "get_tuning_configuration",
    "get_slow_queries",
    "get_maintenance_status",
    "get_index_health",
}


def make_config() -> BlueprintConfig:
    dsn = os.environ.get("MCP_BLUEPRINT_MYSQL_URL", "mysql://monitor@localhost:3306/mysakila")
    return BlueprintConfig(
        server=ServerConfig(packs_dir=str(PROJECT_ROOT / "packs")),
        database=DatabaseConfig(engine="mysql", dsn=dsn),
        logging=LoggingConfig(level="warning"),
    )


@pytest.fixture
async def blueprint() -> Blueprint:
    bp = Blueprint(config=make_config())
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"MySQL not reachable: {exc}")
    bp.load_packs()
    yield bp
    await bp.close()


async def test_every_pack_tool_executes(blueprint: Blueprint) -> None:
    assert set(blueprint.list_tools()) == EXPECTED_TOOLS
    for tool_name in blueprint.list_tools():
        result = await blueprint.pipeline.execute(tool_name, {})
        assert result["status"] == "success", tool_name
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
