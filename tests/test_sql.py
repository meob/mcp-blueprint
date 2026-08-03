"""Unit tests for the SQL loader and Jinja2 renderer."""

from __future__ import annotations

import pytest

from blueprint.errors import SQLLoadError, SQLRenderError
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer


def test_sql_loader_resolves_relative_to_tool(tmp_path) -> None:
    sql_dir = tmp_path / "sql"
    sql_dir.mkdir()
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir()
    (sql_dir / "query.sql").write_text("SELECT 1", encoding="utf-8")
    loader = SQLLoader()
    tool_source = str(tools_dir / "get_data.yaml")
    sql = loader.load("../sql/query.sql", tool_source)
    assert sql == "SELECT 1"


def test_sql_loader_missing_file(tmp_path) -> None:
    loader = SQLLoader()
    tool_source = str(tmp_path / "tools" / "get_data.yaml")
    with pytest.raises(SQLLoadError):
        loader.load("../sql/missing.sql", tool_source)


def test_renderer_plain_sql() -> None:
    renderer = SQLRenderer()
    assert renderer.render("SELECT 1", {}) == "SELECT 1"


def test_renderer_conditional_filter() -> None:
    renderer = SQLRenderer()
    template = "SELECT * FROM t\n{% if database %}\nWHERE datname = %(database)s\n{% endif %}"
    rendered = renderer.render(template, {"database": "pgbench"})
    assert "WHERE datname = %(database)s" in rendered
    rendered_empty = renderer.render(template, {"database": None})
    assert "WHERE" not in rendered_empty


def test_renderer_undefined_variable_raises() -> None:
    renderer = SQLRenderer()
    with pytest.raises(SQLRenderError):
        renderer.render("WHERE x = {{ missing }}", {})


def test_renderer_conditional_like_filter() -> None:
    renderer = SQLRenderer()
    template = "SELECT * FROM t\n{% if object_name %}\nWHERE name LIKE %(object_name)s\n{% endif %}"
    rendered = renderer.render(template, {"object_name": "%payment%"})
    assert "LIKE %(object_name)s" in rendered
    rendered_empty = renderer.render(template, {"object_name": None})
    assert "WHERE" not in rendered_empty
