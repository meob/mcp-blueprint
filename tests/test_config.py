"""Unit tests for configuration loading."""

from __future__ import annotations

import pytest

from blueprint.config import (
    DatabaseConfig,
    ServerConfig,
    load_config,
    load_database_config,
    load_yaml,
)
from blueprint.errors import ConfigurationError


def test_server_config_defaults() -> None:
    config = ServerConfig()
    assert config.name == "mcp-blueprint"
    assert config.transport == "stdio"
    assert config.default_ttl == 30
    assert config.packs is None


def test_server_config_packs_from_list() -> None:
    config = ServerConfig(packs=["sakila", "pg-dba"])
    assert config.packs == ["sakila", "pg-dba"]


def test_server_config_packs_from_csv_string() -> None:
    config = ServerConfig(packs="sakila, pg-dba")
    assert config.packs == ["sakila", "pg-dba"]


def test_server_config_packs_empty_means_all() -> None:
    config = ServerConfig(packs=" , ")
    assert config.packs is None


def test_server_config_packs_unknown_type_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ServerConfig(packs=123)


def test_invalid_transport_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ServerConfig(transport="carrier-pigeon")


def test_database_dsn_parts(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("MCP_BLUEPRINT_DATABASE_URL", raising=False)
    config = DatabaseConfig(
        engine="postgresql",
        host="db.internal",
        port=5433,
        dbname="app",
        user="alice",
        password="s3cret",
    )
    dsn = config.resolved_dsn
    assert dsn == "postgresql://alice:s3cret@db.internal:5433/app"


def test_database_env_var_override(monkeypatch) -> None:
    monkeypatch.setenv("MCP_BLUEPRINT_DATABASE_URL", "postgresql://override@localhost/app")
    config = DatabaseConfig(engine="postgresql")
    assert config.resolved_dsn == "postgresql://override@localhost/app"


def test_yaml_env_expansion(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MY_DSN", "postgresql://fromenv/db")
    file_path = tmp_path / "database.yaml"
    file_path.write_text("database:\n  dsn: ${MY_DSN}\n", encoding="utf-8")
    config = load_database_config(file_path)
    assert config.dsn == "postgresql://fromenv/db"


def test_missing_file_raises(tmp_path) -> None:
    with pytest.raises(ConfigurationError):
        load_yaml(tmp_path / "missing.yaml")


def test_load_config_from_directory(tmp_path) -> None:
    (tmp_path / "server.yaml").write_text("server:\n  name: my-server\n", encoding="utf-8")
    (tmp_path / "database.yaml").write_text(
        "database:\n  engine: postgresql\n  dsn: postgresql://pgbench@localhost/db\n",
        encoding="utf-8",
    )
    (tmp_path / "logging.yaml").write_text("logging:\n  level: debug\n", encoding="utf-8")
    config = load_config(tmp_path)
    assert config.server.name == "my-server"
    assert config.database.engine == "postgresql"
    assert config.logging.level == "debug"


def test_load_config_single_embedded_file(tmp_path) -> None:
    file_path = tmp_path / "server.yaml"
    file_path.write_text(
        "server:\n  name: embedded\ndatabase:\n  engine: postgresql\nlogging:\n  level: info\n",
        encoding="utf-8",
    )
    config = load_config(file_path)
    assert config.server.name == "embedded"
    assert config.database.engine == "postgresql"
