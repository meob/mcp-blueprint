"""Shared fixtures and a fake database adapter for pipeline tests."""

from __future__ import annotations

from typing import Any

import pytest

from blueprint.db.base import DatabaseAdapter
from blueprint.tools.model import ToolMetadata


class FakeAdapter(DatabaseAdapter):
    """In-memory adapter that records executed SQL and returns canned rows."""

    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []
        self.executed: list[tuple[str, dict[str, Any]]] = []
        self.closed = False
        self.fail: Exception | None = None

    async def execute(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        self.executed.append((sql, params))
        if self.fail is not None:
            raise self.fail
        return list(self.rows)

    async def test_connection(self) -> None:
        self.executed.append(("SELECT 1 AS ok", {}))

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def adapter() -> FakeAdapter:
    return FakeAdapter()


@pytest.fixture
def metadata() -> ToolMetadata:
    return ToolMetadata(
        name="get_test_data",
        description="Test tool.",
        parameters={
            "database": {"type": "string", "required": False, "default": None},
            "min_rows": {"type": "integer", "required": True, "default": None},
        },
        sql="sql/test.sql",
        pack_name="test-pack",
        source="packs/test-pack/tools/get_test_data.yaml",
    )
