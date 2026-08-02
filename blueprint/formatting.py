"""Result formatting and JSON-safe serialization.

Raw SQL rows are rarely ideal for LLM consumption.  Formatters rename columns,
drop internal columns, convert byte counts to human-readable sizes and convert
non-JSON values (dates, decimals, durations) into strings.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from blueprint.tools.model import FormatConfig


def human_size(value: int | float) -> str:
    """Convert a byte count into a human-readable string like ``12.5 MB``."""
    value = float(value)
    units = ["B", "KB", "MB", "GB", "TB", "PB"]
    for unit in units:
        if abs(value) < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} B"


def json_safe(value: Any) -> Any:
    """Convert a value into a JSON-serializable representation."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return str(value)


class ResultFormatter:
    """Applies configured formatting rules to result rows."""

    def apply(self, rows: list[dict[str, Any]], fmt: FormatConfig | None) -> list[dict[str, Any]]:
        """Return a formatted copy of ``rows`` applying ``fmt`` rules."""
        if not fmt:
            return rows
        rows = [self._rename(row, fmt.rename) for row in rows]
        if fmt.hidden:
            rows = [{k: v for k, v in row.items() if k not in fmt.hidden} for row in rows]
        if fmt.convert_size:
            rows = [self._convert_size(row, fmt.convert_size) for row in rows]
        return rows

    @staticmethod
    def _rename(row: dict[str, Any], mapping: dict[str, str]) -> dict[str, Any]:
        if not mapping:
            return row
        return {mapping.get(key, key): value for key, value in row.items()}

    @staticmethod
    def _convert_size(row: dict[str, Any], columns: list[str]) -> dict[str, Any]:
        updated = dict(row)
        for column in columns:
            value = updated.get(column)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                updated[column] = human_size(value)
        return updated
