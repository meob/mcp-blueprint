"""Offline conformance tests for the multi-engine DBA packs.

These tests never touch a database.  They verify, for every tool in the
oracle, clickhouse, sqlserver and mariadb packs, that:

* the tool manifest and the matching SQL file both exist;
* the SQL passes the static security guard (single read-only statement);
* the engine-specific placeholder syntax renders correctly for the tools
  that accept parameters.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from blueprint.db.placeholders import to_oracle, to_pyodbc
from blueprint.sql.guard import ensure_single_statement, statement_kind, validate_template
from blueprint.tools.loader import load_tools_from_dir

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PACKS = {
    "oracle-dba": "oracle",
    "clickhouse-dba": "clickhouse",
    "sqlserver-dba": "sqlserver",
    "mariadb-dba": "mariadb",
}

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


@pytest.mark.parametrize("pack_name", sorted(PACKS))
def test_pack_exposes_all_thirteen_tools(pack_name: str) -> None:
    tools = load_tools_from_dir(
        str(PROJECT_ROOT / "packs" / pack_name / "tools"), pack_name=pack_name
    )
    assert {tool.name for tool in tools} == EXPECTED_TOOLS


@pytest.mark.parametrize("pack_name", sorted(PACKS))
def test_every_tool_has_matching_sql_file(pack_name: str) -> None:
    tools = load_tools_from_dir(
        str(PROJECT_ROOT / "packs" / pack_name / "tools"), pack_name=pack_name
    )
    for tool in tools:
        sql_path = (Path(tool.source).parent / tool.sql).resolve()
        assert sql_path.is_file(), f"{pack_name}/{tool.name}: missing {sql_path.name}"


@pytest.mark.parametrize("pack_name", sorted(PACKS))
def test_pack_manifest_declares_expected_engine(pack_name: str) -> None:
    manifest_path = PROJECT_ROOT / "packs" / pack_name / "pack.yaml"
    manifest = yaml.safe_load(manifest_path.read_text())
    assert manifest["engines"] == [PACKS[pack_name]]


@pytest.mark.parametrize(
    "pack_name", sorted(PACKS), ids=lambda p: p.replace("-dba", "")
)
def test_all_sql_is_single_read_only_statement(pack_name: str) -> None:
    sql_dir = PROJECT_ROOT / "packs" / pack_name / "sql"
    files = sorted(sql_dir.glob("*.sql"))
    assert len(files) == len(EXPECTED_TOOLS)
    for path in files:
        sql = path.read_text()
        validate_template(sql)
        ensure_single_statement(sql)
        assert statement_kind(sql) == "read", path.name
        assert path.stem in EXPECTED_TOOLS


def _render_largest_objects(pack_name: str, params: dict) -> str:
    sql = (PROJECT_ROOT / "packs" / pack_name / "sql" / "get_largest_objects.sql").read_text()
    from jinja2 import Template

    return Template(sql).render(params)


def test_oracle_renders_bind_colon_placeholders() -> None:
    rendered = _render_largest_objects("oracle-dba", {"object_name": "EMP%"})
    oracle_sql = to_oracle(rendered)
    assert "LIKE :object_name" in oracle_sql
    assert "%(object_name)s" not in oracle_sql

    no_filter = to_oracle(_render_largest_objects("oracle-dba", {}))
    assert "WHERE" not in no_filter
    assert "%(" not in no_filter


def test_sqlserver_renders_positional_placeholders() -> None:
    rendered = _render_largest_objects("sqlserver-dba", {"object_name": "EMP%"})
    pyodbc_sql, params = to_pyodbc(rendered, {"object_name": "EMP%"})
    assert "LIKE ?" in pyodbc_sql
    assert params == ["EMP%"]

    no_filter_sql, no_filter_params = to_pyodbc(_render_largest_objects("sqlserver-dba", {}), {})
    assert "?" not in no_filter_sql
    assert no_filter_params == []


@pytest.mark.parametrize("pack_name", ["clickhouse-dba", "mariadb-dba"])
def test_named_placeholder_packs_keep_native_syntax(pack_name: str) -> None:
    rendered = _render_largest_objects(pack_name, {"object_name": "EMP%"})
    assert "%(object_name)s" in rendered
    assert to_oracle(rendered) != rendered
