"""Blueprint application entry point.

The :class:`Blueprint` class loads configuration, discovers packs, builds the
execution pipeline and exposes a FastMCP server.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from blueprint import server as server_module
from blueprint.cache import Cache
from blueprint.config import (
    BlueprintConfig,
    load_config,
)
from blueprint.db.base import DatabaseAdapter, create_adapter
from blueprint.errors import ConfigurationError, ToolLoadError, ToolSecurityError
from blueprint.formatting import ResultFormatter
from blueprint.logging import configure_logging
from blueprint.pack import load_pack_metadata
from blueprint.pipeline import ToolPipeline
from blueprint.sql.guard import ensure_read_only, ensure_single_statement, validate_template
from blueprint.sql.loader import SQLLoader
from blueprint.sql.renderer import SQLRenderer
from blueprint.tools.loader import load_tools_from_dir
from blueprint.tools.model import ToolMetadata
from blueprint.tools.registry import ToolRegistry


class Blueprint:
    """Framework facade: configuration, packs, pipeline and transports."""

    def __init__(
        self, config: BlueprintConfig | None = None, config_path: str | Path | None = None
    ) -> None:
        self.config = config or load_config(config_path)
        self.logger = configure_logging(self.config.logging)
        self.registry = ToolRegistry()
        self.sql_loader = SQLLoader()
        self.renderer = SQLRenderer()
        self.cache = Cache(maxsize=self.config.server.cache_maxsize)
        self.formatter = ResultFormatter()
        self._adapter: DatabaseAdapter | None = None

    def load_packs(self, packs_dir: str | Path | None = None) -> int:
        """Discover and register all tools from ``packs_dir``.

        Each subdirectory is treated as a pack; tools are loaded from its
        ``tools`` directory.  Packs whose ``pack.yaml`` declares engines that
        do not match the configured engine are skipped.  Returns the number of
        registered tools.
        """
        directory = Path(packs_dir or self.config.server.packs_dir)
        if not directory.is_dir():
            raise ConfigurationError(f"packs directory not found: {directory}")

        engine = self.config.database.engine_id
        count = 0
        for pack_dir in sorted(directory.iterdir()):
            if not pack_dir.is_dir():
                continue
            tools_dir = pack_dir / "tools"
            if not tools_dir.is_dir():
                continue
            metadata = load_pack_metadata(pack_dir)
            if not metadata.supports(engine):
                self.logger.info("pack_skipped_for_engine", pack=pack_dir.name, engine=engine)
                continue
            allowed = self.config.server.packs
            if allowed is not None and pack_dir.name not in allowed:
                self.logger.info("pack_skipped_by_config", pack=pack_dir.name)
                continue
            tools = load_tools_from_dir(tools_dir, pack_name=pack_dir.name, engine=engine)
            for tool in tools:
                self._validate_tool_sql(tool)
            self.registry.register_many(tools)
            count += len(tools)
            self.logger.info("pack_loaded", pack=pack_dir.name, tools=len(tools))
        return count

    def load_pack(self, pack_dir: str | Path) -> int:
        """Register tools from a single pack directory.

        The pack is skipped when its ``pack.yaml`` declares engines that do not
        match the configured engine.
        """
        directory = Path(pack_dir)
        metadata = load_pack_metadata(directory)
        if not metadata.supports(self.config.database.engine_id):
            self.logger.info(
                "pack_skipped_for_engine",
                pack=directory.name,
                engine=self.config.database.engine_id,
            )
            return 0
        tools = load_tools_from_dir(
            directory / "tools",
            pack_name=directory.name,
            engine=self.config.database.engine_id,
        )
        for tool in tools:
            self._validate_tool_sql(tool)
        self.registry.register_many(tools)
        self.logger.info("pack_loaded", pack=directory.name, tools=len(tools))
        return len(tools)

    def _validate_tool_sql(self, metadata: ToolMetadata) -> None:
        """Enforce the SQL safety policy on a tool's static templates.

        Every SQL file must avoid value interpolation and, unless the tool
        declares ``writes: true``, must be a single read-only statement.
        Runtime enforcement in the pipeline cannot be bypassed; this load-time
        check surfaces authoring errors early with the tool name.
        """
        paths = [metadata.sql] if isinstance(metadata.sql, str) else list(metadata.sql.values())
        for path in paths:
            sql = self.sql_loader.load(path, metadata.source)
            try:
                validate_template(sql)
                if metadata.writes:
                    ensure_single_statement(sql)
                else:
                    ensure_read_only(sql)
            except ToolSecurityError as exc:
                raise ToolLoadError(
                    f"tool '{metadata.name}' in pack '{metadata.pack_name}' ({path}): {exc}"
                ) from exc

    @property
    def adapter(self) -> DatabaseAdapter:
        """Return the database adapter, creating it on first use."""
        if self._adapter is None:
            self._adapter = create_adapter(self.config.database)
        return self._adapter

    @property
    def pipeline(self) -> ToolPipeline:
        """Return the execution pipeline for the current configuration."""
        return ToolPipeline(
            registry=self.registry,
            sql_loader=self.sql_loader,
            renderer=self.renderer,
            adapter=self.adapter,
            formatter=self.formatter,
            cache=self.cache,
            default_ttl=self.config.server.default_ttl,
            max_rows=self.config.server.max_rows,
        )

    def list_tools(self) -> list[str]:
        """Return the names of all registered tools."""
        return [tool.name for tool in self.registry.all()]

    def create_server(self, host: str | None = None, port: int | None = None) -> FastMCP:
        """Build a FastMCP server with all enabled tools registered.

        ``host`` and ``port`` override the configured values and only apply to
        the streamable HTTP transport.
        """
        return server_module.create_server(
            self.pipeline,
            self.registry,
            self.config.server.name,
            host=host or self.config.server.host,
            port=port or self.config.server.port,
        )

    async def test_connection(self) -> None:
        """Verify the configured database is reachable."""
        await self.adapter.test_connection()

    async def close(self) -> None:
        """Release all framework resources."""
        if self._adapter is not None:
            await self._adapter.close()
            self._adapter = None

    async def __aenter__(self) -> Blueprint:
        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()
