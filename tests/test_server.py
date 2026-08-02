"""Unit tests for FastMCP dynamic tool registration."""

from __future__ import annotations

from pathlib import Path

from blueprint import server as server_module
from blueprint.cache import Cache
from blueprint.formatting import ResultFormatter
from blueprint.pipeline import ToolPipeline
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer
from blueprint.tools.model import ToolMetadata
from blueprint.tools.registry import ToolRegistry
from tests.conftest import FakeAdapter


def make_metadata(tmp_path: Path) -> ToolMetadata:
    (tmp_path / "data.sql").write_text("SELECT 1", encoding="utf-8")
    return ToolMetadata(
        name="get_data",
        description="Test tool.",
        parameters={
            "database": {"type": "string", "required": False, "default": None},
            "limit": {"type": "integer", "required": False, "default": 10},
        },
        sql=str(tmp_path / "data.sql"),
        source=str(tmp_path / "get_data.yaml"),
    )


def build_pipeline(registry: ToolRegistry, rows: list[dict] | None = None) -> ToolPipeline:
    return ToolPipeline(
        registry=registry,
        sql_loader=SQLLoader(),
        renderer=SQLRenderer(),
        adapter=FakeAdapter(rows=rows or []),
        formatter=ResultFormatter(),
        cache=Cache(),
    )


async def test_tool_registration_schema(tmp_path) -> None:
    registry = ToolRegistry()
    metadata = make_metadata(tmp_path)
    registry.register(metadata)
    mcp = server_module.create_server(build_pipeline(registry), registry, "test")

    tools = await mcp.list_tools()
    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "get_data"
    assert tool.description == "Test tool."
    schema = tool.inputSchema
    database_schema = schema["properties"]["database"]
    assert database_schema["anyOf"] == [{"type": "string"}, {"type": "null"}]
    limit_schema = schema["properties"]["limit"]
    assert "integer" in [entry["type"] for entry in limit_schema["anyOf"]]
    assert "database" not in schema.get("required", [])


async def test_tool_call_routes_to_correct_handler(tmp_path) -> None:
    registry = ToolRegistry()
    metadata = make_metadata(tmp_path)
    metadata.parameters["limit"].required = True
    registry.register(metadata)

    pipeline = build_pipeline(registry, rows=[{"value": 42}])
    mcp = server_module.create_server(pipeline, registry, "test")

    result = await mcp.call_tool("get_data", {"database": "pgbench", "limit": 5})
    assert result[0].text is not None
    assert '"tool": "get_data"' in result[0].text


async def test_tool_without_parameters_registers(tmp_path) -> None:
    registry = ToolRegistry()
    (tmp_path / "nop.sql").write_text("SELECT 1", encoding="utf-8")
    metadata = ToolMetadata(
        name="no_params",
        description="No params.",
        sql=str(tmp_path / "nop.sql"),
        source=str(tmp_path / "nop.yaml"),
    )
    registry.register(metadata)

    mcp = server_module.create_server(build_pipeline(registry), registry, "test")
    tools = await mcp.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "no_params"
