"""Unit tests for result formatting and JSON-safe serialization."""

from __future__ import annotations

from datetime import datetime

from blueprint.formatting import ResultFormatter, human_size, json_safe
from blueprint.tools.model import FormatConfig


def test_human_size() -> None:
    assert human_size(0) == "0 B"
    assert human_size(512) == "512 B"
    assert human_size(1024) == "1.0 KB"
    assert human_size(10 * 1024 * 1024) == "10.0 MB"


def test_format_rename_hidden_convert() -> None:
    rows = [{"old_name": 2048, "secret": "x", "keep": 1}]
    fmt = FormatConfig(rename={"old_name": "size"}, hidden=["secret"], convert_size=["size"])
    result = ResultFormatter().apply(rows, fmt)
    assert result == [{"size": "2.0 KB", "keep": 1}]


def test_no_format_returns_rows() -> None:
    rows = [{"a": 1}]
    assert ResultFormatter().apply(rows, None) is rows


def test_json_safe_scalars() -> None:
    assert json_safe(1) == 1
    assert json_safe(None) is None
    assert json_safe("x") == "x"
    assert json_safe(True) is True


def test_json_safe_complex_values() -> None:
    value = {
        "when": datetime(2026, 1, 2, 3, 4, 5),
        "amount": 1.5,
        "blob": b"abc",
    }
    safe = json_safe(value)
    assert safe["when"] == "2026-01-02T03:04:05"
    assert safe["amount"] == 1.5
    assert safe["blob"] == "abc"
