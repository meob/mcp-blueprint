"""Command line interface.

Examples:

.. code-block:: bash

   blueprint list-tools --config config/server.yaml
   blueprint serve --config config/server.yaml --transport stdio
   blueprint serve --config config/server.yaml --transport http --port 8000
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence

from blueprint.app import Blueprint
from blueprint.errors import BlueprintError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blueprint", description="Domain-oriented MCP server framework."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list-tools", help="list the tools provided by the configured packs"
    )
    list_parser.add_argument("--config", default="config", help="configuration directory or file")

    serve_parser = subparsers.add_parser("serve", help="run the MCP server")
    serve_parser.add_argument("--config", default="config", help="configuration directory or file")
    serve_parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default=None,
        help="override the configured transport",
    )
    serve_parser.add_argument("--host", default=None, help="override the HTTP bind host")
    serve_parser.add_argument("--port", type=int, default=None, help="override the HTTP bind port")

    return parser


async def _run(list_tools_only: bool, args: argparse.Namespace) -> int:
    blueprint = Blueprint(config_path=args.config)
    blueprint.load_packs()

    if list_tools_only:
        for name in blueprint.list_tools():
            print(name)
        return 0

    transport = args.transport or blueprint.config.server.transport
    if transport == "http":
        transport = "streamable-http"

    await blueprint.test_connection()

    if transport == "streamable-http":
        host = args.host or blueprint.config.server.host
        port = args.port or blueprint.config.server.port
        server = blueprint.create_server(host, port)
        print(f"serving MCP tools on '{transport}' at http://{host}:{port}/mcp", file=sys.stderr)
        await server.run_streamable_http_async()
    else:
        server = blueprint.create_server()
        print("serving MCP tools on 'stdio'", file=sys.stderr)
        await server.run_stdio_async()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return asyncio.run(_run(args.command == "list-tools", args))
    except BlueprintError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
