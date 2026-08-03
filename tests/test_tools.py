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


def test_engine_filtering_sql_mapping(tmp_path) -> None:
    tool_file = tmp_path / "pg.yaml"
    tool_file.write_text(
        "name: get_x\ndescription: x\nsql:\n  postgresql: ../sql/postgresql/get_x.sql\n",
        encoding="utf-8",
    )
    tool = load_tool_from_file(tool_file, engine="postgresql")
    assert tool is not None
    assert tool.sql_for("postgresql") == "../sql/postgresql/get_x.sql"
    assert tool.sql_for("mysql") is None
    assert load_tool_from_file(tool_file, engine="mysql") is None


def test_engine_filtering_shared_sql(tmp_path) -> None:
    tool_file = tmp_path / "shared.yaml"
    tool_file.write_text("name: get_y\ndescription: y\nsql: ../sql/get_y.sql\n", encoding="utf-8")
    assert load_tool_from_file(tool_file, engine="postgresql") is not None
    assert load_tool_from_file(tool_file, engine="mysql") is not None


def test_engine_filtering_restricted(tmp_path) -> None:
    tool_file = tmp_path / "z.yaml"
    tool_file.write_text(
        "name: get_z\ndescription: z\nengines:\n  - postgresql\nsql: ../sql/get_z.sql\n",
        encoding="utf-8",
    )
    assert load_tool_from_file(tool_file, engine="postgresql") is not None
    assert load_tool_from_file(tool_file, engine="mysql") is None


def test_engines_must_match_sql_mapping(tmp_path) -> None:
    tool_file = tmp_path / "bad.yaml"
    tool_file.write_text(
        "name: get_w\n"
        "description: w\n"
        "engines:\n"
        "  - postgresql\n"
        "sql:\n"
        "  oracle: ../sql/oracle/get_w.sql\n",
        encoding="utf-8",
    )
    try:
        load_tool_from_file(tool_file)
    except ToolLoadError as exc:
        assert "must match" in str(exc)
    else:
        raise AssertionError("expected ToolLoadError")


def test_load_tools_from_dir_filters_by_engine(tmp_path) -> None:
    (tmp_path / "a.yaml").write_text(
        "name: tool_a\ndescription: a\nsql:\n  postgresql: ../sql/a.sql\n", encoding="utf-8"
    )
    (tmp_path / "b.yaml").write_text(
        "name: tool_b\ndescription: b\nsql: ../sql/b.sql\n", encoding="utf-8"
    )
    tools = load_tools_from_dir(tmp_path, pack_name="demo", engine="mysql")
    assert [t.name for t in tools] == ["tool_b"]


def test_app_loads_only_engine_matching_packs() -> None:
    from pathlib import Path

    from blueprint.app import Blueprint
    from blueprint.config import BlueprintConfig, DatabaseConfig, ServerConfig

    project_root = Path(__file__).resolve().parents[1]
    config = BlueprintConfig(
        server=ServerConfig(packs_dir=str(project_root / "packs")),
        database=DatabaseConfig(engine="mysql", dsn="mysql://localhost/app"),
    )
    app = Blueprint(config=config)
    assert app.load_packs() == 12
    assert {tool.pack_name for tool in app.registry.all()} == {"mysql-dba"}

    postgres = Blueprint(config_path=str(project_root / "config"))
    assert postgres.load_packs() == 16
    assert {tool.pack_name for tool in postgres.registry.all()} == {"pg-dba", "sakila"}


def test_template_pack_stays_loadable() -> None:
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[1]
    tools_dir = project_root / "template" / "pack" / "tools"
    tools = load_tools_from_dir(tools_dir, pack_name="my-pack", engine="postgresql")
    assert [t.name for t in tools] == ["get_items"]
    assert tools[0].sql_for("postgresql") == "../sql/get_items.sql"
