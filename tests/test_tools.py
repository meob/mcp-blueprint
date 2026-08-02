"""Unit tests for tool loading and the tool registry."""

from __future__ import annotations

from blueprint.errors import ToolLoadError, ToolNotFoundError
from blueprint.tools.loader import load_tool_from_file, load_tools_from_dir
from blueprint.tools.registry import ToolRegistry


def test_load_valid_tool(tmp_path) -> None:
    tool_file = tmp_path / "get_data.yaml"
    tool_file.write_text(
        "name: get_data\n"
        "description: Fetch some data.\n"
        "parameters:\n"
        "  limit:\n"
        "    type: integer\n"
        "    required: true\n"
        "sql: ../sql/get_data.sql\n"
        "cache:\n"
        "  ttl: 10\n",
        encoding="utf-8",
    )
    tool = load_tool_from_file(tool_file, pack_name="demo")
    assert tool.name == "get_data"
    assert tool.pack_name == "demo"
    assert tool.source.endswith("get_data.yaml")
    assert tool.parameters["limit"].type == "integer"
    assert tool.parameters["limit"].required is True
    assert tool.cache is not None and tool.cache.ttl == 10


def test_invalid_tool_name_rejected(tmp_path) -> None:
    tool_file = tmp_path / "bad.yaml"
    tool_file.write_text("name: 'Bad-Name'\ndescription: x\nsql: a.sql\n", encoding="utf-8")
    try:
        load_tool_from_file(tool_file)
    except ToolLoadError as exc:
        assert "invalid tool definition" in str(exc)
    else:
        raise AssertionError("expected ToolLoadError")


def test_missing_sql_field_rejected(tmp_path) -> None:
    tool_file = tmp_path / "bad2.yaml"
    tool_file.write_text("name: get_data\ndescription: x\n", encoding="utf-8")
    try:
        load_tool_from_file(tool_file)
    except ToolLoadError:
        pass
    else:
        raise AssertionError("expected ToolLoadError")


def test_load_all_tools_from_dir(tmp_path) -> None:
    for name in ("a", "b", "c"):
        (tmp_path / f"tool_{name}.yaml").write_text(
            f"name: tool_{name}\ndescription: {name}\nsql: ../sql/tool_{name}.sql\n",
            encoding="utf-8",
        )
    tools = load_tools_from_dir(tmp_path, pack_name="demo")
    assert [t.name for t in tools] == ["tool_a", "tool_b", "tool_c"]


def test_registry_roundtrip(metadata) -> None:
    registry = ToolRegistry()
    registry.register(metadata)
    assert registry.get("get_test_data") is metadata
    assert registry.enabled() == [metadata]
    registry.unregister("get_test_data")
    try:
        registry.get("get_test_data")
    except ToolNotFoundError:
        pass
    else:
        raise AssertionError("expected ToolNotFoundError")


def test_registry_overwrite_warns(metadata) -> None:
    registry = ToolRegistry()
    registry.register(metadata)
    registry.register(metadata)
    assert len(registry.all()) == 1
