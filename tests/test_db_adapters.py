"""Unit tests for the Oracle, ClickHouse, SQL Server and MariaDB adapters.

The optional database drivers are not required: imports are stubbed and
queries run against fake connections.
"""

from __future__ import annotations

import asyncio
import sys

import pytest

from blueprint.config import DatabaseConfig
from blueprint.db.base import create_adapter
from blueprint.db.clickhouse import ClickHouseAdapter
from blueprint.db.mariadb import MariaDBAdapter
from blueprint.db.oracle import OracleAdapter
from blueprint.db.sqlserver import SQLServerAdapter
from blueprint.errors import AdapterNotFoundError, DatabaseError


@pytest.fixture(autouse=True)
def _no_external_dsn(monkeypatch) -> None:
    monkeypatch.delenv("MCP_BLUEPRINT_DATABASE_URL", raising=False)


def make_config(**kwargs) -> DatabaseConfig:
    return DatabaseConfig(**kwargs)


# --- factory routing ------------------------------------------------------


@pytest.mark.parametrize(
    ("engine", "adapter_type"),
    [
        ("oracle", OracleAdapter),
        ("clickhouse", ClickHouseAdapter),
        ("sqlserver", SQLServerAdapter),
        ("mariadb", MariaDBAdapter),
    ],
)
def test_create_adapter_routes_new_engines(engine: str, adapter_type: type) -> None:
    adapter = create_adapter(make_config(engine=engine))
    assert isinstance(adapter, adapter_type)
    assert adapter.engine == engine


def test_create_adapter_accepts_mssql_alias() -> None:
    assert isinstance(create_adapter(make_config(engine="mssql")), SQLServerAdapter)


def test_create_adapter_unknown_engine_raises() -> None:
    config = make_config(engine="postgresql")
    config.engine = "db2"
    with pytest.raises(AdapterNotFoundError):
        create_adapter(config)


# --- connection configuration ---------------------------------------------


def test_oracle_kwargs_from_dsn() -> None:
    adapter = OracleAdapter(make_config(engine="oracle", dsn="oracle://scott:tiger@db:1521/ORCL"))
    assert adapter._connection_kwargs() == {
        "user": "scott",
        "password": "tiger",
        "dsn": "db:1521/ORCL",
    }


def test_oracle_kwargs_default_port_when_unset() -> None:
    adapter = OracleAdapter(make_config(engine="oracle", dsn="oracle://scott:tiger@db/ORCL"))
    assert adapter._connection_kwargs()["dsn"] == "db:1521/ORCL"


def test_oracle_kwargs_from_parts_ignores_pg_default_port() -> None:
    adapter = OracleAdapter(make_config(engine="oracle", host="db", port=5432, dbname="ORCL"))
    assert adapter._connection_kwargs()["dsn"] == "db:1521/ORCL"


def test_clickhouse_kwargs_from_dsn() -> None:
    adapter = ClickHouseAdapter(
        make_config(engine="clickhouse", dsn="clickhouse://user:pw@ch:9000/analytics")
    )
    assert adapter._connection_kwargs() == {
        "host": "ch",
        "port": 9000,
        "user": "user",
        "password": "pw",
        "database": "analytics",
    }


def test_clickhouse_kwargs_default_port_when_unset() -> None:
    adapter = ClickHouseAdapter(make_config(engine="clickhouse", dsn="clickhouse://u:p@ch"))
    assert adapter._connection_kwargs()["port"] == 9000


def test_sqlserver_connection_string_uses_default_port() -> None:
    adapter = SQLServerAdapter(
        make_config(engine="sqlserver", host="sqldb", dbname="app", user="sa", password="pw")
    )
    conn_string = adapter._connection_string()
    assert "SERVER=sqldb,1433;" in conn_string
    assert "DATABASE=app;" in conn_string
    assert "Encrypt=optional;" in conn_string


# --- missing optional driver ----------------------------------------------


@pytest.mark.parametrize(
    ("engine", "driver", "expected_hint"),
    [
        ("oracle", "oracledb", "[oracle]"),
        ("clickhouse", "clickhouse_driver", "[clickhouse]"),
        ("sqlserver", "pyodbc", "[sqlserver]"),
    ],
)
async def test_missing_driver_reports_extra(
    engine: str, driver: str, expected_hint: str, monkeypatch
) -> None:
    monkeypatch.setitem(sys.modules, driver, None)
    adapter = create_adapter(make_config(engine=engine))
    with pytest.raises(DatabaseError) as exc_info:
        await adapter.test_connection()
    assert expected_hint in str(exc_info.value)


# --- execute behaviour ------------------------------------------------------


async def test_oracle_execute_lowercases_columns_and_translates_placeholders(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeCursor:
        description = [("COLUMN_ONE",), ("ColumnTwo",)]

        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *exc_info: object) -> None:
            return None

        async def execute(self, sql: str, params: object) -> None:
            captured["sql"] = sql
            captured["params"] = params

        async def fetchall(self) -> list[tuple]:
            return [(1, "x")]

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

    class FakePool:
        def acquire(self) -> FakePool:
            return self

        async def __aenter__(self) -> FakeConnection:
            return FakeConnection()

        async def __aexit__(self, *exc_info: object) -> None:
            return None

    adapter = OracleAdapter(make_config(engine="oracle"))
    monkeypatch.setattr(adapter, "_get_pool", async_fake(FakePool()))

    rows = await adapter.execute("SELECT %(val)s AS column_one FROM dual", {"val": 1})
    assert rows == [{"column_one": 1, "columntwo": "x"}]
    assert captured["sql"] == "SELECT :val AS column_one FROM dual"
    assert captured["params"] == {"val": 1}


async def test_clickhouse_execute_binds_none_when_no_params(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeClient:
        def execute(self, sql: str, params: object, with_column_types: bool = False):
            captured["sql"] = sql
            captured["params"] = params
            return ([(1,)], [("num", "UInt8")])

        def disconnect(self) -> None:
            return None

    adapter = ClickHouseAdapter(make_config(engine="clickhouse"))
    monkeypatch.setattr(adapter, "_get_client", async_fake(FakeClient()))

    rows = await adapter.execute("SELECT 1 AS num", {})
    assert rows == [{"num": 1}]
    assert captured["params"] is None


async def test_sqlserver_execute_uses_positional_params(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakeCursor:
        description = [("A",), ("B",)]

        def execute(self, sql: str, values: object) -> None:
            captured["sql"] = sql
            captured["values"] = values

        def fetchall(self) -> list[tuple]:
            return [(1, 2)]

        def close(self) -> None:
            return None

    class FakeConnection:
        def cursor(self) -> FakeCursor:
            return FakeCursor()

    async def fake_acquire() -> FakeConnection:
        return FakeConnection()

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    adapter = SQLServerAdapter(make_config(engine="sqlserver"))
    adapter._queue = asyncio.Queue()
    monkeypatch.setattr(adapter, "_acquire", fake_acquire)
    monkeypatch.setattr(asyncio, "to_thread", fake_to_thread)

    rows = await adapter.execute("SELECT %(v)s AS a, 2 AS b", {"v": 9})
    assert rows == [{"A": 1, "B": 2}]
    assert captured["sql"] == "SELECT ? AS a, 2 AS b"
    assert captured["values"] == [9]


def async_fake(obj: object):
    async def _fake() -> object:
        return obj

    return _fake
