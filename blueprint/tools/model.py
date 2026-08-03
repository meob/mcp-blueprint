"""Pydantic models describing tool metadata.

A tool is described by a YAML file with no Python code required.  This module
defines the schema used to validate those files.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from blueprint.engines import SUPPORTED_ENGINES

ParameterType = Literal["string", "integer", "number", "boolean"]

PYTHON_ANNOTATION: dict[str, str] = {
    "string": "str",
    "integer": "int",
    "number": "float",
    "boolean": "bool",
}


class ParameterSpec(BaseModel):
    """A single tool parameter."""

    type: ParameterType = "string"
    required: bool = False
    default: Any = None
    description: str | None = None

    @field_validator("default")
    @classmethod
    def _default_matches_type(cls, value: Any, info: Any) -> Any:
        param_type = info.data.get("type", "string")
        if value is None:
            return value
        try:
            return _COERCERS[param_type](value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"default {value!r} is not a valid {param_type}") from exc

    def python_annotation(self) -> str:
        """Return the Python annotation string for this parameter."""
        base = PYTHON_ANNOTATION[self.type]
        return f"{base} | None" if not self.required else base


_COERCERS: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


class CacheConfig(BaseModel):
    """Per-tool cache policy."""

    ttl: int | None = None


class FormatConfig(BaseModel):
    """Optional result formatting rules."""

    rename: dict[str, str] = Field(default_factory=dict)
    hidden: list[str] = Field(default_factory=list)
    convert_size: list[str] = Field(default_factory=list)


class ToolMetadata(BaseModel):
    """Full tool definition loaded from YAML."""

    name: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    description: str = ""
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)
    sql: str | dict[str, str]
    engines: list[str] = Field(default_factory=list)
    cache: CacheConfig | None = None
    roles: list[str] = Field(default_factory=list)
    enabled: bool = True
    requires_confirmation: bool = False
    writes: bool = False
    format: FormatConfig | None = None
    pack_name: str = ""
    source: str = ""

    @field_validator("engines")
    @classmethod
    def _validate_engines(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        for engine in value:
            if not engine or engine in seen:
                raise ValueError(f"duplicate or empty engine: {engine!r}")
            if engine not in SUPPORTED_ENGINES:
                raise ValueError(f"unsupported engine: {engine}")
            seen.add(engine)
        return value

    @field_validator("sql")
    @classmethod
    def _validate_sql(cls, value: str | dict[str, str]) -> str | dict[str, str]:
        if isinstance(value, dict):
            if not value:
                raise ValueError("sql mapping must not be empty")
            for engine, path in value.items():
                if engine not in SUPPORTED_ENGINES:
                    raise ValueError(f"unsupported sql engine: {engine}")
                if not path:
                    raise ValueError(f"sql path is empty for engine {engine}")
        return value

    @model_validator(mode="after")
    def _check_engines_sql_consistency(self) -> ToolMetadata:
        if isinstance(self.sql, dict) and self.engines and set(self.engines) != set(self.sql):
            raise ValueError("engines must match the sql mapping keys when both are given")
        return self

    def applies_to(self, engine: str) -> bool:
        """Whether this tool is available for the given engine."""
        if isinstance(self.sql, dict):
            return engine in self.sql
        return not self.engines or engine in self.engines

    def sql_for(self, engine: str) -> str | None:
        """Return the SQL path for ``engine``, or ``None`` when not applicable."""
        if isinstance(self.sql, dict):
            return self.sql.get(engine)
        return self.sql if self.applies_to(engine) else None
