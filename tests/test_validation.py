"""Unit tests for parameter validation."""

from __future__ import annotations

import pytest

from blueprint.errors import ToolValidationError
from blueprint.tools.model import ToolMetadata
from blueprint.validation import validate_parameters


def make_metadata() -> ToolMetadata:
    return ToolMetadata(
        name="t",
        sql="x.sql",
        parameters={
            "name": {"type": "string", "required": True},
            "count": {"type": "integer", "required": False, "default": 5},
            "ratio": {"type": "number", "required": False, "default": None},
            "verbose": {"type": "boolean", "required": False, "default": False},
        },
    )


def test_required_and_defaults() -> None:
    params = validate_parameters(make_metadata(), {"name": "app"})
    assert params == {"name": "app", "count": 5, "ratio": None, "verbose": False}


def test_missing_required_raises() -> None:
    with pytest.raises(ToolValidationError, match="missing required parameter 'name'"):
        validate_parameters(make_metadata(), {})


def test_unknown_parameter_raises() -> None:
    with pytest.raises(ToolValidationError, match="unknown parameter"):
        validate_parameters(make_metadata(), {"name": "a", "bogus": 1})


def test_integer_coercion() -> None:
    params = validate_parameters(make_metadata(), {"name": "a", "count": "42"})
    assert params["count"] == 42
    assert isinstance(params["count"], int)


def test_boolean_coercion() -> None:
    params = validate_parameters(make_metadata(), {"name": "a", "verbose": "true"})
    assert params["verbose"] is True


def test_invalid_integer_raises() -> None:
    with pytest.raises(ToolValidationError):
        validate_parameters(make_metadata(), {"name": "a", "count": "not-a-number"})
