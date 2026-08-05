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

SAKILA_TOOLS = {
    "customer_account_summary",
    "film_stock",
    "recommend_films",
    "rental_history",
    "search_customer",
}


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


async def test_search_customer(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("search_customer", {"name": "hunter"})
    assert result["status"] == "success"
    assert result["row_count"] >= 1
    for row in result["rows"]:
        full_name = (row["first_name"] + row["last_name"]).upper()
        assert "HUNTER" in full_name


async def test_search_customer_full_name(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("search_customer", {"name": "tammy sanders"})
    assert result["status"] == "success"
    assert result["row_count"] == 1
    assert result["rows"][0]["customer_id"] == 75


async def test_search_customer_unknown_returns_empty(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("search_customer", {"name": "nobody-lives-here"})
    assert result["status"] == "success"
    assert result["row_count"] == 0


async def test_customer_account_summary(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("customer_account_summary", {"customer_name": "tammy sanders"})
    assert result["status"] == "success"
    assert result["row_count"] == 1
    row = result["rows"][0]
    assert row["customer_id"] == 75
    assert row["total_rentals"] >= row["open_rentals"]
    assert row["standing"] in {"GOOD STANDING", "HAS OVERDUE"}
    assert row["standing"] == "HAS OVERDUE"
    assert "(OVERDUE)" in row["open_films"]


async def test_customer_account_summary_unknown_returns_empty(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("customer_account_summary", {"customer_name": "nobody-lives-here"})
    assert result["status"] == "success"
    assert result["row_count"] == 0


async def test_rental_history(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("rental_history", {"customer_name": "tammy sanders"})
    assert result["status"] == "success"
    assert 0 < result["row_count"] <= 25
    statuses = {row["status"] for row in result["rows"]}
    assert statuses <= {"active", "overdue", "returned"}
    assert "overdue" in statuses


async def test_recommend_films_generic(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("recommend_films", {"category": "Family", "count": 3})
    assert result["status"] == "success"
    assert result["row_count"] == 3
    popularity = [row["popularity"] for row in result["rows"]]
    assert popularity == sorted(popularity, reverse=True)
    for row in result["rows"]:
        assert row["available_copies"] >= 1


async def test_recommend_films_excludes_rented(blueprint: Blueprint) -> None:
    rented = await blueprint.pipeline.execute("rental_history", {"customer_name": "tammy sanders"})
    rented_titles = {row["title"] for row in rented["rows"]}
    result = await blueprint.pipeline.execute("recommend_films", {"customer_name": "tammy sanders", "count": 5})
    assert result["status"] == "success"
    assert result["row_count"] > 0
    assert rented_titles.isdisjoint({row["title"] for row in result["rows"]})


async def test_recommend_films_rating_filter(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("recommend_films", {"rating": "G", "count": 5})
    assert result["status"] == "success"
    assert result["row_count"] > 0
    assert all(row["rating"] == "G" for row in result["rows"])


async def test_film_stock(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("film_stock", {"title": "academy dinosaur"})
    assert result["status"] == "success"
    assert result["row_count"] == 2
    for row in result["rows"]:
        assert row["total_copies"] >= row["available"]
        assert 0 <= row["available"] <= row["total_copies"]


async def test_film_stock_single_store(blueprint: Blueprint) -> None:
    result = await blueprint.pipeline.execute("film_stock", {"title": "academy dinosaur", "store_id": 1})
    assert result["status"] == "success"
    assert result["row_count"] == 1
    assert result["rows"][0]["store_id"] == 1
