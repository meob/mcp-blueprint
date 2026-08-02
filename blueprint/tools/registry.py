"""In-memory registry of loaded tools."""

from __future__ import annotations

from collections.abc import Iterable

import structlog

from blueprint.errors import ToolNotFoundError
from blueprint.tools.model import ToolMetadata

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """Stores and queries :class:`ToolMetadata` instances by name."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolMetadata] = {}

    def register(self, tool: ToolMetadata) -> None:
        """Register a tool, replacing any previous definition with the same name."""
        if tool.name in self._tools:
            logger.warning(
                "tool_overwritten",
                tool=tool.name,
                previous=tool.name,
                source=self._tools[tool.name].source,
            )
        self._tools[tool.name] = tool

    def register_many(self, tools: Iterable[ToolMetadata]) -> None:
        """Register several tools at once."""
        for tool in tools:
            self.register(tool)

    def unregister(self, name: str) -> None:
        """Remove a tool by name."""
        self._tools.pop(name, None)

    def get(self, name: str) -> ToolMetadata:
        """Return a tool by name or raise :class:`ToolNotFoundError`."""
        try:
            return self._tools[name]
        except KeyError as exc:
            raise ToolNotFoundError(f"unknown tool: {name}") from exc

    def all(self) -> list[ToolMetadata]:
        """Return all registered tools."""
        return list(self._tools.values())

    def enabled(self) -> list[ToolMetadata]:
        """Return all enabled tools."""
        return [tool for tool in self._tools.values() if tool.enabled]

    def clear(self) -> None:
        """Remove all registered tools."""
        self._tools.clear()
