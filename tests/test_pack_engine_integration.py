"""Integration tests for the oracle, clickhouse, sqlserver and mariadb packs.

Each engine is tested against a live database when reachable, and skipped
otherwise.  The connection is taken from ``MCP_BLUEPRINT_<ENGINE>_URL`` (e.g.
``MCP_BLUEPRINT_ORACLE_URL``) and falls back to a local default.
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
    "get_connections",
    "get_database_sizes",
    "get_database_version",
    "get_largest_objects",
    "get_replication_status",
    "get_tuning_configuration",
    "get_slow_queries",
    "get_maintenance_status",
    "get_index_health",
}

ENGINES = {
    "oracle": ("oracle-dba", "oracle://monitor:monitor_pw@localhost:1521/FREEPDB1"),
    "clickhouse": ("clickhouse-dba", "clickhouse://monitor:monitor_pw@localhost:9000/default"),
    "sqlserver": ("sqlserver-dba", "sqlserver://sa:YourStrong!Passw0rd@localhost:1433/master"),
    "mariadb": ("mariadb-dba", "mariadb://monitor:monitor_pw@localhost:3307/mysakila"),
}

KPI_COLUMNS = {"kpi_name", "current_value", "unit", "suggested_threshold", "status"}


def make_config(engine: str) -> BlueprintConfig:
    env_name = f"MCP_BLUEPRINT_{engine.upper()}_URL"
    dsn = os.environ.get(env_name, ENGINES[engine][1])
    return BlueprintConfig(
        server=ServerConfig(packs_dir=str(PROJECT_ROOT / "packs")),
        database=DatabaseConfig(engine=engine, dsn=dsn),
        logging=LoggingConfig(level="warning"),
    )


@pytest.mark.parametrize("engine", sorted(ENGINES))
async def test_every_pack_tool_executes(engine: str) -> None:
    pack_name, _ = ENGINES[engine]
    bp = Blueprint(config=make_config(engine))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"{engine} not reachable: {exc}")
    bp.load_packs()
    try:
        assert set(bp.list_tools()) == EXPECTED_TOOLS
        for tool_name in bp.list_tools():
            result = await bp.pipeline.execute(tool_name, {})
            assert result["status"] == "success", f"{pack_name}/{tool_name}"
            assert result["row_count"] == len(result["rows"])
    finally:
        await bp.close()


@pytest.mark.parametrize("engine", sorted(ENGINES))
async def test_kpi_tools_return_status_rows(engine: str) -> None:
    bp = Blueprint(config=make_config(engine))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"{engine} not reachable: {exc}")
    bp.load_packs()
    try:
        for tool_name in ("get_operational_kpis", "get_performance_kpis", "get_security_kpis"):
            result = await bp.pipeline.execute(tool_name, {})
            assert result["row_count"] > 0, f"{engine}/{tool_name}"
            for row in result["rows"]:
                assert set(row) == KPI_COLUMNS, f"{engine}/{tool_name}"
                assert row["status"] in {"ok", "warning", "error"}, f"{engine}/{tool_name}"
    finally:
        await bp.close()


@pytest.mark.parametrize("engine", sorted(ENGINES))
async def test_replication_tool_reports_instance(engine: str) -> None:
    bp = Blueprint(config=make_config(engine))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"{engine} not reachable: {exc}")
    bp.load_packs()
    try:
        result = await bp.pipeline.execute("get_replication_status", {})
        assert result["row_count"] > 0
        components = {row["component"] for row in result["rows"]}
        assert all(components), "every component must be non-empty"
        # The packs use engine-specific topology naming: PostgreSQL-family
        # engines report an 'instance' component, ClickHouse reports
        # 'cluster' (and 'replica' only when replicated tables exist).
        expected = {"cluster"} if engine == "clickhouse" else {"instance"}
        assert components.issuperset(expected)
    finally:
        await bp.close()


@pytest.mark.parametrize("engine", sorted(ENGINES))
async def test_largest_objects_ordered_and_filterable(engine: str) -> None:
    bp = Blueprint(config=make_config(engine))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"{engine} not reachable: {exc}")
    bp.load_packs()
    try:
        unfiltered = await bp.pipeline.execute("get_largest_objects", {})
        assert unfiltered["row_count"] > 0
        sizes = [row["size_bytes"] for row in unfiltered["rows"]]
        assert sizes == sorted(sizes, reverse=True)
        assert len(unfiltered["rows"]) <= 32

        prefix = unfiltered["rows"][0]["name"][:4]
        filtered = await bp.pipeline.execute(
            "get_largest_objects", {"object_name": f"{prefix}%"}
        )
        assert filtered["status"] == "success"
        assert all(row["name"].startswith(prefix) for row in filtered["rows"])
        assert filtered["row_count"] <= unfiltered["row_count"]
    finally:
        await bp.close()


@pytest.mark.parametrize("engine", sorted(ENGINES))
async def test_database_version_returns_three_columns(engine: str) -> None:
    bp = Blueprint(config=make_config(engine))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"{engine} not reachable: {exc}")
    bp.load_packs()
    try:
        result = await bp.pipeline.execute("get_database_version", {})
        assert result["row_count"] == 1
        row = result["rows"][0]
        assert set(row) == {"version", "version_number", "full_version"}
        assert row["version"]
        assert str(row["version_number"]).isdigit()
        assert row["version"] in row["full_version"]
    finally:
        await bp.close()
