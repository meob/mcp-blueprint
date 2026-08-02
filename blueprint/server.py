"""FastMCP integration.

Tools are registered dynamically from YAML metadata.  For every tool a typed
async function is generated so that FastMCP infers the correct JSON schema,
validates parameters and documents the tool automatically.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

import structlog
from mcp.server.fastmcp import FastMCP

from blueprint.pipeline import ToolPipeline
from blueprint.tools.model import ToolMetadata
from blueprint.tools.registry import ToolRegistry

logger = structlog.get_logger(__name__)

Handler = Callable[..., Awaitable[dict[str, Any]]]


def build_tool_function(
    handler: Handler, metadata: ToolMetadata
) -> Callable[..., Awaitable[dict[str, Any]]]:
    """Generate a typed async function for the given tool metadata.

    Required parameters precede optional ones so the resulting signature is
    always valid Python.  Arguments are keyword-only.
    """
    items = list(metadata.parameters.items())
    required = [(name, spec) for name, spec in items if spec.required]
    optional = [(name, spec) for name, spec in items if not spec.required]

    args: list[str] = []
    for name, spec in required:
        args.append(f"{name}: {spec.python_annotation()}")
    for name, spec in optional:
        args.append(f"{name}: {spec.python_annotation()} = {spec.default!r}")

    signature = f"(*, {', '.join(args)})" if args else "()"
    calls = ", ".join(f"{name}={name}" for name, _ in items)
    source = f"async def _tool{signature}:\n    return await _handler({calls})\n"
    namespace: dict[str, Any] = {"_handler": handler}
    exec(compile(source, f"<tool:{metadata.name}>", "exec"), namespace)

    fn = cast(Callable[..., Awaitable[dict[str, Any]]], namespace["_tool"])
    fn.__name__ = metadata.name
    fn.__qualname__ = metadata.name
    return fn


def register_tools(mcp: FastMCP, pipeline: ToolPipeline, registry: ToolRegistry) -> int:
    """Register every enabled tool on the FastMCP server.

    Returns the number of registered tools.
    """
    count = 0
    for metadata in registry.enabled():

        async def handler(_metadata: ToolMetadata = metadata, **kwargs: Any) -> dict[str, Any]:
            return await pipeline.execute(_metadata.name, kwargs)

        fn = build_tool_function(handler, metadata)
        mcp.add_tool(fn, name=metadata.name, description=metadata.description or metadata.name)
        logger.info("tool_registered", tool=metadata.name)
        count += 1
    return count


def create_server(
    pipeline: ToolPipeline,
    registry: ToolRegistry,
    server_name: str,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> FastMCP:
    """Create a FastMCP server with all enabled tools registered."""
    mcp = FastMCP(server_name, host=host, port=port)
    register_tools(mcp, pipeline, registry)
    return mcp
