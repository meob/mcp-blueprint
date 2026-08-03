"""FastMCP integration.

Tools are registered dynamically from YAML metadata.  For every tool a typed
async function is generated so that FastMCP infers the correct JSON schema,
validates parameters and documents the tool automatically.

FastMCP validates arguments against the generated schema before the handler
runs, so rejected calls would otherwise escape the audit trail.  The server
therefore validates parameters first, through the framework's own validator,
so every rejected call is still recorded as ``tool_failed``.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any, cast

import structlog
import structlog.contextvars
from mcp.server.fastmcp import FastMCP

from blueprint.errors import ToolNotFoundError, ToolValidationError
from blueprint.logging import record_audit
from blueprint.metrics import Metrics
from blueprint.pipeline import ToolPipeline
from blueprint.tools.model import ToolMetadata
from blueprint.tools.registry import ToolRegistry
from blueprint.validation import validate_parameters

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


class AuditedFastMCP(FastMCP):
    """FastMCP server that audits parameter-validation rejections.

    FastMCP rejects arguments that do not match the generated schema before
    the tool handler runs, bypassing the pipeline audit trail.  Parameters are
    validated here first, using the framework's own validator, so every
    rejected call is recorded as ``tool_failed`` and then returned to the
    client as an error.
    """

    def __init__(
        self,
        registry: ToolRegistry,
        server_name: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        metrics: Metrics | None = None,
    ) -> None:
        super().__init__(server_name, host=host, port=port)
        self._registry = registry
        self._metrics = metrics

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Validate before FastMCP does, so rejected calls stay in the audit log."""
        try:
            metadata = self._registry.get(name)
        except ToolNotFoundError:
            metadata = None

        if metadata is not None:
            started = perf_counter()
            structlog.contextvars.clear_contextvars()
            structlog.contextvars.bind_contextvars(trace_id=uuid.uuid4().hex)
            try:
                validate_parameters(metadata, arguments)
            except ToolValidationError as exc:
                record_audit(
                    "tool_failed",
                    tool=name,
                    pack=metadata.pack_name,
                    params=arguments or {},
                    duration_ms=round((perf_counter() - started) * 1000, 2),
                    status="error",
                    error=str(exc),
                )
                if self._metrics is not None:
                    self._metrics.record_error(
                        name, metadata.pack_name, round((perf_counter() - started) * 1000, 2)
                    )
                raise
            finally:
                structlog.contextvars.clear_contextvars()

        return await super().call_tool(name, arguments)


def create_server(
    pipeline: ToolPipeline,
    registry: ToolRegistry,
    server_name: str,
    host: str = "127.0.0.1",
    port: int = 8000,
    metrics: Metrics | None = None,
) -> FastMCP:
    """Create a FastMCP server with all enabled tools registered."""
    mcp = AuditedFastMCP(registry, server_name, host=host, port=port, metrics=metrics)
    register_tools(mcp, pipeline, registry)
    return mcp
