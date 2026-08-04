"""Unit tests for the ``examples/customers`` example pack.

The example pack must load without a live database: registering tools only
parses metadata and validates the SQL templates against the read-only policy.
"""

from __future__ import annotations

from pathlib import Path

from blueprint.app import Blueprint
from blueprint.config import BlueprintConfig, DatabaseConfig, LoggingConfig, ServerConfig
from blueprint.pack import load_pack_metadata

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = PROJECT_ROOT / "examples" / "customers"

EXPECTED_TOOLS = {
    "search_customers",
    "get_customer",
    "get_customer_orders",
    "get_orders_kpis",
}


def make_blueprint() -> Blueprint:
    config = BlueprintConfig(
        server=ServerConfig(name="customers-test"),
        database=DatabaseConfig(
            engine="postgresql", dsn="postgresql://user:pass@localhost:5432/customers"
        ),
        logging=LoggingConfig(level="warning"),
    )
    return Blueprint(config=config)


async def test_example_pack_registers_all_tools() -> None:
    bp = make_blueprint()
    try:
        assert bp.load_pack(PACK_DIR) == len(EXPECTED_TOOLS)
        assert set(bp.list_tools()) == EXPECTED_TOOLS
    finally:
        await bp.close()


def test_example_pack_metadata_is_complete() -> None:
    metadata = load_pack_metadata(PACK_DIR)
    assert metadata.name == "customers"
    assert metadata.version
    assert metadata.description
    assert metadata.instructions
    assert metadata.supports("postgresql")
    assert not metadata.supports("mysql")


async def test_example_tools_have_descriptions_and_parameters() -> None:
    bp = make_blueprint()
    try:
        bp.load_pack(PACK_DIR)
        tools = {tool.name: tool for tool in bp.registry.all()}
        for name in EXPECTED_TOOLS:
            assert tools[name].description
            assert tools[name].sql
        assert set(tools["search_customers"].parameters) == {"name", "city"}
        assert tools["get_customer"].parameters["customer_id"].required
        assert set(tools["get_customer_orders"].parameters) == {"customer_id", "status"}
    finally:
        await bp.close()
