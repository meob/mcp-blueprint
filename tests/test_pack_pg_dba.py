"""Integration tests against a live PostgreSQL instance.

These tests are skipped when the database is not reachable.  The target
connection is taken from the ``MCP_BLUEPRINT_DATABASE_URL`` environment
variable or from the project ``config/database.yaml`` file.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from blueprint.app import Blueprint
from blueprint.errors import DatabaseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
async def blueprint() -> Blueprint:
    bp = Blueprint(config_path=str(PROJECT_ROOT / "config"))
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"PostgreSQL not reachable: {exc}")
    bp.load_packs()
    yield bp
    await bp.close()


async def test_every_pack_tool_executes(blueprint: Blueprint) -> None:
    assert len(blueprint.list_tools()) == 7
    pipeline = blueprint.pipeline
    for tool_name in blueprint.list_tools():
        params = {"database": "pgbench"} if tool_name != "get_replication_status" else {}
        if tool_name == "get_long_running_queries":
            params["min_seconds"] = 0
        result = await pipeline.execute(tool_name, params)
        assert result["status"] == "success", tool_name
        assert "rows" in result
        assert result["row_count"] == len(result["rows"])


async def test_get_database_size_formats_bytes(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_database_size", {"database": "pgbench"})
    row = result["rows"][0]
    assert row["database"] == "pgbench"
    assert "MB" in row["size"] or "KB" in row["size"] or "GB" in row["size"]


async def test_stdlib_server_registers_tools(blueprint: Blueprint) -> None:
    from mcp.server.fastmcp import FastMCP

    server = blueprint.create_server()
    assert isinstance(server, FastMCP)
    tools = await server.list_tools()
    assert {tool.name for tool in tools} == set(blueprint.list_tools())
