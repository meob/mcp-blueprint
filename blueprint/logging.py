"""Structured logging setup.

Logs are written to ``stderr`` by default; under the stdio transport
``stdout`` is reserved for the MCP protocol stream and must never be used for
logging.

By default nothing is persisted: a single JSON (or console) stream on stderr.
``LoggingConfig.file_path`` adds a rotating file handler for the main log.
``LoggingConfig.audit`` enables a dedicated audit channel that records one
JSON line per tool execution.

Every event carries a ``trace_id`` bound per tool call (see the pipeline) so
records from a single request can be correlated.  Sensitive values are masked
by default through :func:`redact_secrets`.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

import structlog
import structlog.contextvars

from blueprint.config import AuditConfig, LoggingConfig

_configured = False
_audit_enabled = False

_SENSITIVE_SUBSTRINGS = (
    "password",
    "passwd",
    "pwd",
    "secret",
    "token",
    "apikey",
    "api_key",
    "authorization",
    "credential",
    "private_key",
    "access_key",
    "dsn",
    "connstring",
    "connection_string",
)


def _is_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(word in lowered for word in _SENSITIVE_SUBSTRINGS)


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if _is_sensitive(str(key)) else _redact(item) for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


def redact_secrets(
    _logger: Any, _method: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any] | str | bytes | bytearray | tuple[Any, ...]:
    """Mask values whose keys identify sensitive data, recursively."""
    return cast(MutableMapping[str, Any], _redact(event_dict))


def _shared_processors() -> list[structlog.types.Processor]:
    return [
        structlog.contextvars.merge_contextvars,
        redact_secrets,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]


def _make_formatter(renderer: structlog.types.Processor) -> structlog.stdlib.ProcessorFormatter:
    return structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=_shared_processors(),
    )


def _ensure_dir(path: str) -> None:
    """Create the parent directory of ``path`` if it does not exist."""
    parent = Path(path).expanduser().parent
    parent.mkdir(parents=True, exist_ok=True)


def configure_logging(config: LoggingConfig | None = None) -> structlog.stdlib.BoundLogger:
    """Configure structlog and stdlib logging.

    Safe to call multiple times; structlog is configured once, while the
    handlers are (re)attached on every call.
    """
    global _configured, _audit_enabled
    config = config or LoggingConfig()
    _audit_enabled = bool(config.audit and config.audit.enabled)

    level = getattr(logging, config.level.upper(), logging.INFO)

    if config.format == "console":
        renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    else:
        renderer = structlog.processors.JSONRenderer()

    if not _configured:
        structlog.configure(
            processors=[
                *_shared_processors(),
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        _configured = True

    formatter = _make_formatter(renderer)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    handlers[0].setFormatter(formatter)

    if config.file_path:
        _ensure_dir(config.file_path)
        file_handler = RotatingFileHandler(
            config.file_path,
            maxBytes=config.file_max_bytes,
            backupCount=config.file_backups,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    root = logging.getLogger()
    root.handlers = handlers
    root.setLevel(level)

    _configure_audit_logger(config)

    return cast(structlog.stdlib.BoundLogger, structlog.get_logger())


def _configure_audit_logger(config: LoggingConfig) -> None:
    audit_logger = logging.getLogger("audit")
    if not config.audit or not config.audit.enabled:
        audit_logger.handlers = []
        audit_logger.propagate = False
        audit_logger.setLevel(logging.CRITICAL + 1)
        return
    audit: AuditConfig = config.audit
    _ensure_dir(audit.file_path)
    handler = RotatingFileHandler(
        audit.file_path,
        maxBytes=audit.max_bytes,
        backupCount=audit.backups,
        encoding="utf-8",
    )
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.JSONRenderer(),
            ],
            foreign_pre_chain=[],
        )
    )
    audit_logger.handlers = [handler]
    audit_logger.propagate = False
    audit_logger.setLevel(logging.INFO)


def audit_enabled() -> bool:
    """Return whether the audit log is active."""
    return _audit_enabled


def get_audit_logger() -> structlog.stdlib.BoundLogger:
    """Return the audit logger, which emits JSONL tool-execution records."""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger("audit"))


def record_audit(event: str, **fields: Any) -> None:
    """Emit one audit record when the audit channel is enabled, otherwise no-op."""
    if _audit_enabled:
        get_audit_logger().info(event, **fields)
