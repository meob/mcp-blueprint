"""Integration tests for the sakila pack against a live Sakila database.

These tests are skipped when the database is not reachable.  The connection
is taken from the ``MCP_BLUEPRINT_SAKILA_URL`` environment variable and falls
back to a local PostgreSQL Sakila database.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from blueprint.app import Blueprint
from blueprint.config import BlueprintConfig, DatabaseConfig, LoggingConfig, ServerConfig
from blueprint.errors import DatabaseError

PROJECT_ROOT = Path(__file__).resolve().parents[1]

SAKILA_TOOLS = {"search_films", "get_film", "search_customer", "get_customer_rentals"}


def make_config() -> BlueprintConfig:
    dsn = os.environ.get("MCP_BLUEPRINT_SAKILA_URL", "postgresql://meo@localhost:5432/sakila")
    return BlueprintConfig(
        server=ServerConfig(packs_dir=str(PROJECT_ROOT / "packs")),
        database=DatabaseConfig(engine="postgresql", dsn=dsn),
        logging=LoggingConfig(level="warning"),
    )


@pytest.fixture
async def blueprint() -> Blueprint:
    bp = Blueprint(config=make_config())
    try:
        await bp.test_connection()
    except DatabaseError as exc:
        pytest.skip(f"Sakila not reachable: {exc}")
    bp.load_packs()
    yield bp
    await bp.close()


async def test_sakila_tools_registered(blueprint: Blueprint) -> None:
    assert set(blueprint.list_tools()) >= SAKILA_TOOLS


async def test_search_films_returns_popular_ordered_rows(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("search_films", {})
    assert result["status"] == "success"
    assert 0 < result["row_count"] <= 20
    popularity = [row["popularity"] for row in result["rows"]]
    assert popularity == sorted(popularity, reverse=True)
    for row in result["rows"]:
        assert {
            "film_id",
            "title",
            "rating_label",
            "min_age",
            "popularity",
            "available_copies",
        } <= set(row)


async def test_search_films_filters(blueprint: Blueprint) -> None:
    by_title = await blueprint.pipeline.execute("search_films", {"title": "gold"})
    assert by_title["row_count"] > 0
    assert all("GOLD" in row["title"] for row in by_title["rows"])

    by_rating = await blueprint.pipeline.execute("search_films", {"rating": "PG-13"})
    assert by_rating["row_count"] > 0
    assert all(row["rating"] == "PG-13" for row in by_rating["rows"])


async def test_get_film_returns_full_record(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_film", {"film_id": 1})
    assert result["status"] == "success"
    assert result["row_count"] == 1
    row = result["rows"][0]
    assert row["film_id"] == 1
    assert row["title"]
    assert row["actors"]
    assert "available" in row["store_availability"]


async def test_get_film_missing_id_returns_empty(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_film", {"film_id": 999999})
    assert result["status"] == "success"
    assert result["row_count"] == 0


async def test_search_customer(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("search_customer", {"name": "hunter"})
    assert result["status"] == "success"
    assert result["row_count"] >= 1
    for row in result["rows"]:
        full_name = (row["first_name"] + row["last_name"]).upper()
        assert "HUNTER" in full_name


async def test_get_customer_rentals_status(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("get_customer_rentals", {"customer_id": 75})
    assert result["status"] == "success"
    assert result["row_count"] > 0
    statuses = {row["status"] for row in result["rows"]}
    assert statuses <= {"active", "overdue", "returned"}
    assert "overdue" in statuses
