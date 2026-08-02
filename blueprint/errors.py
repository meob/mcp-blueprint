"""Exception hierarchy for MCP Blueprint.

Every error raised by the framework derives from :class:`BlueprintError` so
that application code and the MCP layer can handle them uniformly.
"""

from __future__ import annotations


class BlueprintError(Exception):
    """Base class for all framework errors."""


class ConfigurationError(BlueprintError):
    """Raised when configuration is missing, invalid or cannot be loaded."""


class ToolLoadError(BlueprintError):
    """Raised when a tool definition cannot be loaded or parsed."""


class ToolNotFoundError(BlueprintError):
    """Raised when an unknown tool name is requested."""


class ToolValidationError(BlueprintError):
    """Raised when tool parameters fail validation."""


class ToolDisabledError(BlueprintError):
    """Raised when a disabled tool is invoked."""


class SQLLoadError(BlueprintError):
    """Raised when a SQL file cannot be loaded."""


class SQLRenderError(BlueprintError):
    """Raised when a SQL template cannot be rendered."""


class DatabaseError(BlueprintError):
    """Raised when a database operation fails."""


class AdapterNotFoundError(ConfigurationError):
    """Raised when no adapter exists for the configured engine."""


class CacheError(BlueprintError):
    """Raised when a cache operation fails."""
