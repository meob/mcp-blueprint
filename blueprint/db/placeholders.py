"""Placeholder translation for engines that do not speak psycopg3 syntax.

Tool SQL uses psycopg3 named placeholders (``%(name)s``) for every engine.
PostgreSQL, MySQL/MariaDB and ClickHouse accept them natively.  Oracle binds
named parameters with ``:name`` and ODBC (SQL Server / pyodbc) binds
positionally with ``?``.  These helpers translate the psycopg3 style without
touching literal ``%`` characters, which authors escape as ``%%``.
"""

from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER = re.compile(r"%\((?P<name>[A-Za-z_][A-Za-z0-9_]*)\)s")


def to_oracle(sql: str) -> str:
    """Convert ``%(name)s`` placeholders to Oracle ``:name`` binds.

    Literal ``%`` characters written as ``%%`` collapse to a single ``%``.
    """
    return _PLACEHOLDER.sub(r":\g<name>", sql).replace("%%", "%")


def to_pyodbc(sql: str, params: dict[str, Any]) -> tuple[str, list[Any]]:
    """Convert ``%(name)s`` placeholders to ODBC ``?`` markers.

    Returns the translated SQL together with the parameter values in the same
    order the placeholders appear in the statement.  Literal ``%`` characters
    written as ``%%`` collapse to a single ``%``.
    """
    values: list[Any] = []
    translated = _PLACEHOLDER.sub(lambda match: _pyodbc_marker(match, params, values), sql)
    return translated.replace("%%", "%"), values


def _pyodbc_marker(match: re.Match[str], params: dict[str, Any], values: list[Any]) -> str:
    name = match.group("name")
    values.append(params.get(name))
    return "?"
