"""Unit tests for placeholder translation in database adapters."""

from __future__ import annotations

import pytest

from blueprint.db.placeholders import to_oracle, to_pyodbc


def test_to_oracle_translates_named_binds() -> None:
    sql = "SELECT * FROM t WHERE id = %(id)s AND name = %(name)s"
    assert to_oracle(sql) == "SELECT * FROM t WHERE id = :id AND name = :name"


def test_to_oracle_keeps_literal_percent() -> None:
    sql = "SELECT * FROM t WHERE name LIKE %(pattern)s AND pct = '50%%'"
    assert to_oracle(sql) == "SELECT * FROM t WHERE name LIKE :pattern AND pct = '50%'"


def test_to_oracle_untouched_without_placeholders() -> None:
    sql = "SELECT COUNT(*) AS c FROM dual"
    assert to_oracle(sql) == sql


def test_to_pyodbc_converts_to_positional() -> None:
    sql = "SELECT * FROM t WHERE id = %(id)s AND name = %(name)s"
    translated, values = to_pyodbc(sql, {"id": 1, "name": "ann"})
    assert translated == "SELECT * FROM t WHERE id = ? AND name = ?"
    assert values == [1, "ann"]


def test_to_pyodbc_repeats_values_for_repeated_placeholders() -> None:
    sql = "SELECT %(a)s AS x, %(b)s AS y, %(a)s AS z"
    translated, values = to_pyodbc(sql, {"a": 1, "b": 2})
    assert translated == "SELECT ? AS x, ? AS y, ? AS z"
    assert values == [1, 2, 1]


def test_to_pyodbc_keeps_literal_percent() -> None:
    sql = "SELECT * FROM t WHERE name LIKE %(pattern)s AND pct = '50%%'"
    translated, values = to_pyodbc(sql, {"pattern": "a%"})
    assert translated == "SELECT * FROM t WHERE name LIKE ? AND pct = '50%'"
    assert values == ["a%"]


def test_to_pyodbc_missing_param_yields_none() -> None:
    translated, values = to_pyodbc("SELECT %(missing)s", {})
    assert translated == "SELECT ?"
    assert values == [None]


@pytest.mark.parametrize(
    ("placeholder", "oracle"),
    [("%(name)s", ":name"), ("%(a1)s", ":a1"), ("%(_x)s", ":_x")],
)
def test_placeholder_variants(placeholder: str, oracle: str) -> None:
    assert to_oracle(placeholder) == oracle
    translated, _ = to_pyodbc(placeholder, {"name": None, "a1": None, "_x": None})
    assert translated == "?"
