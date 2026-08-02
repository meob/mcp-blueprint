# TODO

This document contains the implementation backlog for **MCP Blueprint**.

Tasks are intentionally small and independent so they can be implemented by AI coding assistants with minimal context switching.

Checkboxes track the current MVP status.

---

# MVP

## Project bootstrap

* [x] Create Python project structure
* [x] Configure pyproject.toml
* [x] Configure Ruff
* [x] Configure Black
* [x] Configure pytest
* [x] Configure mypy
* [x] Configure pre-commit hooks

---

## Core framework

* [x] Create Blueprint application class
* [x] Implement configuration loader
* [x] Implement YAML parser
* [x] Implement SQL loader
* [x] Implement Jinja2 rendering
* [x] Implement parameter validation
* [x] Implement error handling
* [x] Implement structured logging

---

## FastMCP integration

* [x] Initialize FastMCP server
* [x] Automatic tool registration
* [x] Parameter conversion
* [x] Tool documentation generation
* [x] Error propagation
* [x] JSON response formatting

---

## Transport

### stdio

* [x] Implement stdio transport
* [ ] Test with Claude Desktop
* [ ] Test with OpenCode
* [ ] Test with Gemini CLI

### Streamable HTTP

* [x] Implement Streamable HTTP transport
* [x] Configuration options
* [ ] Health endpoint
* [ ] Docker example

---

# Database Layer

## Generic adapter

* [x] Define DatabaseAdapter interface
* [x] Connection abstraction
* [x] Query execution
* [ ] Transaction management
* [x] Connection pooling
* [x] Engine-aware tool loading (`engines`, per-engine `sql` map)

---

## PostgreSQL adapter

* [x] psycopg3 implementation
* [x] Async support
* [x] Connection pool
* [x] Connection testing

---

## Oracle adapter

* [ ] Oracle implementation

---

## ClickHouse adapter

* [ ] ClickHouse implementation

---

## MySQL adapter

* [x] asyncmy implementation
* [x] Async support
* [x] Connection pool
* [x] Connection testing
* [x] DSN and parts-based configuration

---

# Tool System

* [x] YAML tool loader
* [x] Automatic validation
* [x] Parameter parsing
* [x] SQL execution
* [x] Result serialization

---

# SQL Templates

* [x] Jinja2 integration
* [x] Conditional SQL
* [x] Optional parameters
* [x] SQL syntax validation

---

# Formatting

* [x] Column rename support
* [x] Unit conversion
* [x] Timestamp formatting
* [ ] Duration formatting
* [ ] Computed columns
* [x] Hidden columns

---

# Cache

* [x] Cache abstraction
* [x] cachetools backend
* [ ] aiocache backend
* [x] Per-tool TTL
* [ ] Cache invalidation

---

# Security

* [x] Tool enable/disable
* [x] Role metadata
* [x] Confirmation flag
* [ ] Future authentication hooks

---

# Configuration

* [x] server.yaml
* [x] database.yaml
* [x] logging.yaml
* [x] pack.yaml

---

# DBA Pack

The DBA pack (`packs/dba`, formerly `packs/pg-dba`) is the reference
implementation for the framework.  It is cross-database: tools declare the
engines they support via a per-engine `sql` map and are filtered at load time
by the configured engine.  Supported engines: PostgreSQL 14+ and MySQL 8+.

## KPI dashboards

Always return rows with `status` of `ok`/`warning`/`error`.

* [x] get_operational_kpis()
* [x] get_performance_kpis()
* [x] get_security_kpis()

---

## Detail tools

* [x] get_users()
* [x] get_database_sizes()
* [x] get_largest_objects()
* [x] get_replication_status()
* [x] get_tuning_configuration()
* [x] get_slow_queries()
* [x] get_maintenance_status() (cross-engine)
* [x] get_index_health() (postgres-only)

---

## Removed from the original pg-dba pack

* [x] get_connections(), get_active_sessions(), get_blocking_sessions(),
      get_wait_events(), get_long_running_queries() — covered by the KPI
      dashboards and detail tools
* [x] get_wal_backup_status() — checkpoint/backup metrics depend on the
      PostgreSQL minor version; excluded from the static pack

---

## Validated

* [x] All tools run with a non-DBA user (`pg_monitor`) on PostgreSQL
* [x] All tools run with a plain read-only PostgreSQL user
* [x] All tools run on MySQL 8 with a least-privilege monitoring user

---

## Template pack

* [x] `template/pack` skeleton (pack.yaml + example tool + example SQL)
* [x] Not auto-loaded by the framework

---

## Next pack: Sakila

* [ ] Create `packs/sakila` from the template (or the DBA pack layout)

---

# Oracle DBA Pack

* [ ] Initial implementation

---

# SQL Server DBA Pack

* [ ] Initial implementation

---

# MySQL DBA Pack

* [x] Covered by the cross-engine `dba` pack (11 tools on MySQL 8)

---

# Documentation

* [x] Installation guide
* [x] Quick start
* [x] Pack development guide
* [ ] Adapter development guide
* [ ] Contribution guide

---

# Examples

* [x] PostgreSQL example
* [ ] Oracle example
* [ ] Customer Pack example
* [ ] ERP Pack example

---

# Testing

* [x] Unit tests
* [x] Integration tests (PostgreSQL, live instance)
* [x] Integration tests (MySQL, live instance, skipped when unreachable)
* [ ] PostgreSQL CI
* [ ] Oracle CI
* [ ] SQL Server CI
* [ ] MySQL CI

---

# Docker

* [ ] Dockerfile
* [ ] Docker Compose example
* [ ] Streamable HTTP example

---

# Future Features

## Workflow Tools

Higher-level tools orchestrating multiple atomic tools.

Examples:

* [ ] diagnose_performance()
* [ ] diagnose_storage()
* [ ] diagnose_autovacuum()
* [ ] diagnose_replication()

---

## AI-assisted Features

* [ ] Tool self-documentation
* [ ] Automatic OpenAPI-like documentation
* [ ] Tool usage statistics
* [ ] Performance metrics

---

## Nice to Have

* [ ] Plugin system
* [ ] Pack installer
* [ ] Pack repository
* [ ] Web administration UI
* [ ] Metrics endpoint
* [ ] Prometheus integration
* [ ] NoSQL adapters

---

# Long-term Vision

The objective is not simply to create another MCP server.

The objective is to establish a reusable architecture for building domain-oriented MCP servers.

Developers should spend their time defining **tools**, **SQL**, and **business concepts**, while the framework handles infrastructure, transport, validation, caching, formatting, and database abstraction.

Ultimately, adding a new tool should require little more than creating:

* one YAML definition
* one SQL file

without writing additional Python code.
