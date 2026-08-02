"""Pydantic models describing tool metadata.

A tool is described by a YAML file with no Python code required.  This module
defines the schema used to validate those files.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

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
    sql: str
    cache: CacheConfig | None = None
    roles: list[str] = Field(default_factory=list)
    enabled: bool = True
    requires_confirmation: bool = False
    format: FormatConfig | None = None
    pack_name: str = ""
    source: str = ""
