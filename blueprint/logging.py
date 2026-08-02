"""Structured logging setup.

Logs are always written to ``stderr``.  Under the stdio transport ``stdout``
is reserved for the MCP protocol stream and must never be used for logging.
"""

from __future__ import annotations

import logging
import sys
from typing import cast

import structlog

from blueprint.config import LoggingConfig

_configured = False


def configure_logging(config: LoggingConfig | None = None) -> structlog.stdlib.BoundLogger:
    """Configure structlog and return the root logger.

    Safe to call multiple times; only the first call performs configuration.
    """
    global _configured
    config = config or LoggingConfig()

    level = getattr(logging, config.level.upper(), logging.INFO)
    logging.basicConfig(stream=sys.stderr, level=level, format="%(message)s")

    renderer: structlog.types.Processor
    if config.format == "console":
        renderer = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if not _configured:
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        _configured = True

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())
