"""Tool parameter validation and coercion."""

from __future__ import annotations

from typing import Any

from blueprint.errors import ToolValidationError
from blueprint.tools.model import ParameterSpec, ToolMetadata

_TRUE_STRINGS = {"true", "1", "yes", "on"}
_FALSE_STRINGS = {"false", "0", "no", "off"}


def _coerce(value: Any, spec: ParameterSpec) -> Any:
    if value is None:
        return None
    try:
        if spec.type == "string":
            return value if isinstance(value, str) else str(value)
        if spec.type == "integer":
            return int(value)
        if spec.type == "number":
            return float(value)
        if spec.type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                lowered = value.strip().lower()
                if lowered in _TRUE_STRINGS:
                    return True
                if lowered in _FALSE_STRINGS:
                    return False
            return bool(value)
    except (TypeError, ValueError):
        pass
    raise ToolValidationError(f"invalid value {value!r} for parameter of type '{spec.type}'")


def validate_parameters(
    metadata: ToolMetadata, raw_params: dict[str, Any] | None
) -> dict[str, Any]:
    """Validate raw parameters against tool metadata.

    Unknown parameters are rejected, required parameters must be present and
    every value is coerced to the declared type.  Missing optional parameters
    fall back to their declared default.
    """
    raw = dict(raw_params or {})
    unknown = set(raw) - set(metadata.parameters)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ToolValidationError(f"unknown parameter(s) for tool '{metadata.name}': {names}")

    validated: dict[str, Any] = {}
    for name, spec in metadata.parameters.items():
        if name in raw:
            validated[name] = _coerce(raw[name], spec)
        elif spec.required:
            raise ToolValidationError(
                f"missing required parameter '{name}' for tool '{metadata.name}'"
            )
        else:
            validated[name] = spec.default

    return validated
