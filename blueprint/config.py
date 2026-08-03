"""Configuration loading and validation.

Configuration lives in YAML files and can be overridden through environment
variables.  Secrets such as database passwords are never hardcoded: prefer the
``MCP_BLUEPRINT_DATABASE_URL`` environment variable or environment expansion in
the YAML file.
"""

from __future__ import annotations

import os
import re
from functools import cached_property
from pathlib import Path

import structlog
import yaml
from pydantic import BaseModel, Field, field_validator

from blueprint.engines import SUPPORTED_ENGINES
from blueprint.errors import ConfigurationError

logger = structlog.get_logger(__name__)

_ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(?::-([^}]*))?\}")


def _expand_env(value: str) -> str:
    """Expand ``${VAR}`` and ``${VAR:-default}`` references inside a string."""

    def _replace(match: re.Match[str]) -> str:
        var = match.group(1)
        default = match.group(2)
        return (
            os.environ.get(var, default or "") if default is not None else os.environ.get(var, "")
        )

    return _ENV_VAR_PATTERN.sub(_replace, value)


class ServerConfig(BaseModel):
    """Top-level server configuration."""

    name: str = "mcp-blueprint"
    transport: str = "stdio"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "info"
    default_ttl: int | None = 30
    packs_dir: str = "packs"
    cache_maxsize: int = 256
    max_rows: int = 1000
    packs: list[str] | None = None

    @field_validator("transport")
    @classmethod
    def _validate_transport(cls, value: str) -> str:
        if value not in {"stdio", "http", "streamable-http"}:
            raise ValueError(f"unsupported transport: {value}")
        return value

    @field_validator("packs", mode="before")
    @classmethod
    def _validate_packs(cls, value: object) -> list[str] | None:
        """Normalize the pack allowlist from a YAML list or a CSV string."""
        if value is None:
            return None
        if isinstance(value, str):
            names = [item.strip() for item in value.split(",") if item.strip()]
            return names or None
        if isinstance(value, list):
            names = [str(item).strip() for item in value if str(item).strip()]
            return names or None
        raise ValueError(f"invalid packs value: {value!r}")


class PoolConfig(BaseModel):
    """Connection pool settings for the database adapter."""

    min_size: int = 1
    max_size: int = 10
    timeout: float = 30.0


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    engine: str = "postgresql"
    dsn: str = ""
    host: str = "localhost"
    port: int = 5432
    dbname: str = ""
    user: str = ""
    password: str = ""
    pool: PoolConfig = Field(default_factory=PoolConfig)

    @field_validator("engine")
    @classmethod
    def _validate_engine(cls, value: str) -> str:
        if value not in SUPPORTED_ENGINES and value not in {"postgres"}:
            raise ValueError(f"unsupported engine: {value}")
        return value

    @property
    def engine_id(self) -> str:
        """Return the canonical engine identifier used by tool metadata."""
        from blueprint.engines import canonical_engine

        return canonical_engine(self.engine)

    @field_validator("dsn")
    @classmethod
    def _expand_dsn(cls, value: str) -> str:
        return _expand_env(value)

    @cached_property
    def resolved_dsn(self) -> str:
        """Return the effective DSN, preferring an explicit DSN over parts."""
        dsn = os.environ.get("MCP_BLUEPRINT_DATABASE_URL") or self.dsn
        if dsn:
            return dsn
        password = _expand_env(self.password) if self.password else ""
        auth = f"{self.user}:{password}@" if self.user or password else ""
        return f"{self.engine}://{auth}{self.host}:{self.port}/{self.dbname}"


class LoggingConfig(BaseModel):
    """Structured logging configuration."""

    level: str = "info"
    format: str = "json"


class BlueprintConfig(BaseModel):
    """Aggregated framework configuration."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_yaml(path: str | Path) -> dict[str, object]:
    """Load and expand environment variables inside a YAML file."""
    file_path = Path(path)
    if not file_path.is_file():
        raise ConfigurationError(f"configuration file not found: {file_path}")
    try:
        raw = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(_expand_env(raw))
    except yaml.YAMLError as exc:
        raise ConfigurationError(f"invalid YAML in {file_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigurationError(f"configuration file must contain a mapping: {file_path}")
    return data


def load_server_config(path: str | Path | None = None) -> ServerConfig:
    """Load the server configuration section."""
    if path is None:
        return ServerConfig()
    data = load_yaml(path)
    section = data.get("server", data)
    if not isinstance(section, dict):
        raise ConfigurationError(f"server section must be a mapping: {path}")
    return ServerConfig.model_validate(section)


def load_database_config(path: str | Path | None = None) -> DatabaseConfig:
    """Load the database configuration section."""
    if path is None:
        return DatabaseConfig()
    data = load_yaml(path)
    section = data.get("database", data)
    if not isinstance(section, dict):
        raise ConfigurationError(f"database section must be a mapping: {path}")
    return DatabaseConfig.model_validate(section)


def load_logging_config(path: str | Path | None = None) -> LoggingConfig:
    """Load the logging configuration section."""
    if path is None:
        return LoggingConfig()
    data = load_yaml(path)
    section = data.get("logging", data)
    if not isinstance(section, dict):
        raise ConfigurationError(f"logging section must be a mapping: {path}")
    return LoggingConfig.model_validate(section)


def load_config(config_path: str | Path | None = None) -> BlueprintConfig:
    """Load the full framework configuration.

    ``config_path`` may point to:

    * a directory containing ``server.yaml``, ``database.yaml`` and
      ``logging.yaml``;
    * a single ``server.yaml`` that embeds all three sections;
    * a single file with only the ``server`` section (database and logging
      fall back to defaults).
    """
    if config_path is None:
        return BlueprintConfig()

    path = Path(config_path)
    if path.is_dir():
        server_file = path / "server.yaml"
        database_file = path / "database.yaml"
        logging_file = path / "logging.yaml"
        server = load_server_config(server_file) if server_file.is_file() else ServerConfig()
        database = (
            load_database_config(database_file) if database_file.is_file() else DatabaseConfig()
        )
        logging = load_logging_config(logging_file) if logging_file.is_file() else LoggingConfig()
        return BlueprintConfig(server=server, database=database, logging=logging)

    data = load_yaml(path)
    if "server" in data and "database" in data and "logging" in data:
        return BlueprintConfig.model_validate(data)
    return BlueprintConfig(server=ServerConfig.model_validate(data.get("server", data)))
