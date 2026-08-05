"""Unit tests for logging setup, redaction and the audit channel."""

from __future__ import annotations

import json

import structlog

from blueprint.config import AuditConfig, LoggingConfig
from blueprint.logging import (
    audit_enabled,
    configure_logging,
    get_audit_logger,
    redact_secrets,
)


def test_redact_secrets_masks_sensitive_keys() -> None:
    event = {
        "tool": "get_user",
        "params": {
            "customer_id": 42,
            "password": "hunter2",
            "access_token": "abc",
            "nested": {"db_password": "pw", "keep": 1},
            "items": [{"secret": "s1", "ok": True}],
        },
        "dsn": "postgresql://u:p@host/db",
    }
    redacted = redact_secrets(None, "info", dict(event))
    assert redacted["tool"] == "get_user"
    assert redacted["params"]["customer_id"] == 42
    assert redacted["params"]["password"] == "***"
    assert redacted["params"]["access_token"] == "***"
    assert redacted["params"]["nested"] == {"db_password": "***", "keep": 1}
    assert redacted["params"]["items"] == [{"secret": "***", "ok": True}]
    assert redacted["dsn"] == "***"


def test_redact_secrets_keeps_normal_values() -> None:
    event = {"tool": "recommend_films", "params": {"category": "Family"}, "rows": 3}
    assert redact_secrets(None, "info", event) == event


def test_configure_file_logging_writes_jsonl(tmp_path) -> None:
    log_file = tmp_path / "blueprint.jsonl"
    configure_logging(LoggingConfig(file_path=str(log_file)))
    structlog.get_logger("test").info("hello", tool="get_data")
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "hello"
    assert record["tool"] == "get_data"
    assert record["level"] == "info"


def test_configure_file_logging_creates_missing_directory(tmp_path) -> None:
    log_file = tmp_path / "nested" / "logs" / "blueprint.jsonl"
    configure_logging(LoggingConfig(file_path=str(log_file)))
    structlog.get_logger("test").info("hello", tool="get_data")
    assert log_file.is_file()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["event"] == "hello"


def test_configure_audit_writes_jsonl(tmp_path) -> None:
    audit_file = tmp_path / "audit.jsonl"
    configure_logging(LoggingConfig(audit=AuditConfig(enabled=True, file_path=str(audit_file))))
    assert audit_enabled() is True
    get_audit_logger().info(
        "tool_executed",
        tool="customer_account_summary",
        pack="sakila",
        params={"customer_name": "tammy sanders"},
        duration_ms=12.5,
        rows=1,
        status="success",
    )
    lines = audit_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event"] == "tool_executed"
    assert record["tool"] == "customer_account_summary"
    assert record["pack"] == "sakila"
    assert record["status"] == "success"
    assert record["level"] == "info"


def test_audit_disabled_is_inert(tmp_path) -> None:
    audit_file = tmp_path / "audit.jsonl"
    configure_logging(LoggingConfig(audit=AuditConfig(enabled=False, file_path=str(audit_file))))
    assert audit_enabled() is False
    get_audit_logger().info("tool_executed", tool="customer_account_summary")
    assert not audit_file.exists()
