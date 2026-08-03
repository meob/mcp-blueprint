"""Unit tests for the SQL safety guard."""

from __future__ import annotations

import pytest

from blueprint.errors import ToolSecurityError
from blueprint.sql.guard import (
    ensure_read_only,
    ensure_single_statement,
    leading_keyword,
    split_statements,
    statement_kind,
    strip_comments,
    validate_template,
)


def test_statement_kind_read_only() -> None:
    assert statement_kind("SELECT * FROM film") == "read"


def test_statement_kind_with_select_is_read() -> None:
    assert statement_kind("WITH popular AS (SELECT 1) SELECT * FROM popular") == "read"


def test_statement_kind_with_non_select_is_write() -> None:
    sql = "WITH ids AS (SELECT id FROM film) DELETE FROM film WHERE id IN (SELECT id FROM ids)"
    assert statement_kind(sql) == "write"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO film (title) VALUES ('x')",
        "UPDATE film SET title = 'x'",
        "DELETE FROM film",
        "MERGE INTO film USING ...",
        "CALL refresh_materialized_views()",
        "DO $$ BEGIN NULL; END $$",
        "DROP TABLE film",
        "TRUNCATE film",
        "EXPLAIN ANALYZE SELECT 1",
        "SHOW search_path",
        "",
    ],
)
def test_statement_kind_fails_closed_to_write(sql: str) -> None:
    assert statement_kind(sql) == "write"


def test_statement_kind_ignores_comments_and_jinja_blocks() -> None:
    sql = "-- heading\n/* block */ SELECT * FROM film {% if id %}WHERE id = %(id)s{% endif %}"
    assert statement_kind(sql) == "read"


def test_split_statements_ignores_semicolons_in_literals() -> None:
    sql = "SELECT 'a;b' AS v; SELECT 2"
    statements = split_statements(sql)
    assert len(statements) == 2
    assert leading_keyword(statements[0]) == "select"


def test_split_statements_ignores_dollar_quoted_body() -> None:
    sql = "DO $$ BEGIN PERFORM 1; END $$"
    assert len(split_statements(sql)) == 1


def test_ensure_read_only_accepts_single_select() -> None:
    ensure_read_only("SELECT * FROM film ORDER BY title LIMIT 10")


def test_ensure_read_only_rejects_write() -> None:
    with pytest.raises(ToolSecurityError, match="not read-only"):
        ensure_read_only("UPDATE film SET title = 'x'")


def test_ensure_read_only_rejects_stacked_statements() -> None:
    with pytest.raises(ToolSecurityError, match="exactly one statement"):
        ensure_read_only("SELECT 1; DROP TABLE film")


def test_ensure_single_statement_accepts_one() -> None:
    ensure_single_statement("SELECT 1")


def test_ensure_single_statement_rejects_multiple() -> None:
    with pytest.raises(ToolSecurityError, match="exactly one statement"):
        ensure_single_statement("SELECT 1; SELECT 2")


def test_validate_template_accepts_control_flow_only() -> None:
    validate_template("SELECT * FROM t {% if id %}WHERE id = %(id)s{% endif %}")


def test_validate_template_rejects_interpolation() -> None:
    with pytest.raises(ToolSecurityError, match="must not be interpolated"):
        validate_template("SELECT * FROM t WHERE id = {{ user_id }}")


def test_strip_comments_keeps_strings() -> None:
    sql = "SELECT '-- not a comment' FROM t -- tail"
    assert strip_comments(sql) == "SELECT '-- not a comment' FROM t "
