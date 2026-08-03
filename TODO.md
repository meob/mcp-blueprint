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
* [x] Test with OpenCode
* [ ] Test with Gemini CLI

### Streamable HTTP

* [x] Implement Streamable HTTP transport
* [x] Configuration options
* [ ] Health endpoint (see the Docker section; the compose stack uses a TCP
      healthcheck for now)
* [x] Docker example

---

# Database Layer

## Generic adapter

* [x] Define DatabaseAdapter interface
* [x] Connection abstraction
* [x] Query execution
* [ ] Transaction management
* [x] Connection pooling
* [x] Engine-aware pack loading (pack-level `engines`; per-tool `sql` map
      override)

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
* [x] Result size bounded by the framework (`server.max_rows`, default `1000`)
* [ ] Every tool SQL enforces an `ORDER BY` (most significant rows first)
      (`get_largest_objects` already complies; audit the rest)

---

# Formatting

* [x] Column rename support
* [x] Unit conversion
* [x] Timestamp formatting
* [ ] Duration formatting
* [ ] Computed columns
* [x] Hidden columns
* [ ] Human-readable value formatting (e.g. `1000000` -> `1M`) applied
      consistently across engines (PostgreSQL and MySQL currently return
      different `size` formats)

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
* [x] Read-only policy by default: the SQL guard accepts exactly one
      `SELECT` (or a `WITH`/`WITH RECURSIVE` query ending in `SELECT`),
      enforced at load time and re-checked at runtime on the rendered
      statement; fail-closed (`blueprint/sql/guard.py`)
* [x] Writes require an explicit opt-in (`writes: true` in the tool YAML);
      editing the SQL alone is not enough
* [x] Injection hardening: Jinja2 `{{ }}` interpolation is rejected,
      values reach the database only as bound placeholders (`%(name)s`)
* [x] Response row cap `server.max_rows` (default `1000`), configurable
* [x] Unit tests for the guard, pipeline enforcement and load-time
      validation

---

# Configuration

* [x] server.yaml
* [x] database.yaml
* [x] logging.yaml
* [x] pack.yaml

---

# Observability

* [x] Structured JSON logging on stderr (structlog), console format option
* [x] Optional rotating file handler for the main log (`file_path`,
      `file_max_bytes`, `file_backups`)
* [x] Audit channel: one JSONL record per tool execution
      (`tool_executed`/`tool_failed` with tool, pack, params, duration,
      rows, status), disabled by default
* [x] Per-call `trace_id` bound via structlog contextvars, merged into all
      log and audit records
* [x] Sensitive data redaction by default (passwords, tokens, DSNs, ...)
* [x] `docs/logging.md` documenting activation and control
* [x] Prometheus metrics endpoint as an optional `[metrics]` extra: full
      catalog (tool calls/duration/rows, cache hits/misses, DB queries and
      errors, pool stats, registered tools/packs) served on a dedicated
      `host:port/metrics` endpoint that works with stdio too; disabled by
      default (`config/metrics.yaml`); `docs/metrics.md`
* [ ] OpenTelemetry exporter as an optional extra (spans/metrics on top of
      the existing `trace_id`)

---

# Sakila example pack

The recommended first example: a small, domain-oriented pack on PostgreSQL
that lets an agent run a DVD rental store chatbot without writing SQL.  See
`docs/sakila.md` for the full walkthrough.

* [x] Create `packs/sakila` (PostgreSQL, domain-oriented, from a reference pack)
* [x] `search_films(title?, category?, rating?)` — popularity order, rating
      translated to `rating_label`/`min_age` in SQL, `available_copies`
* [x] `get_film(film_id)` — full record with cast, categories and per-store
      availability
* [x] `search_customer(name)`
* [x] `get_customer_rentals(customer_id)` — `active`/`overdue`/`returned` status
* [x] Tool descriptions steer the agent (e.g. `search_customer` points to
      `get_customer_rentals` to check a customer's situation)
* [x] All pack SQL complies with the read-only policy (SELECT only)
* [x] First tools with real parameters: `get_largest_objects` accepts an
      optional `object_name` LIKE filter on both reference DBA packs
* [x] Parameterized SQL escapes literal `%` as `%%` (documented in
      `docs/pack_development.md`) and the pipeline binds only non-`None`
      parameters

---

# Reference DBA Packs

More specialized administration packs.  The reference implementations are two
independent, single-engine packs that expose the same 13 tools:
`packs/pg-dba` (PostgreSQL 14+) and `packs/mysql-dba` (MySQL 8+).  The engine
is declared in `pack.yaml` (`engines: [postgresql]` / `engines: [mysql]`); the
configured engine selects which pack loads.  Each pack is a complete,
copyable example of a Blueprint customization.

## KPI dashboards

Always return rows with `status` of `ok`/`warning`/`error`.

* [x] get_operational_kpis()
* [x] get_performance_kpis()
* [x] get_security_kpis()

---

## Detail tools

* [x] get_users()
* [x] get_connections()
* [x] get_database_sizes()
* [x] get_database_version()
* [x] get_largest_objects()
* [x] get_replication_status()
* [x] get_tuning_configuration()
* [x] get_slow_queries()
* [x] get_maintenance_status()
* [x] get_index_health()

---

## Removed from the original pg-dba pack

* [x] get_active_sessions(), get_blocking_sessions(),
      get_wait_events(), get_long_running_queries() — covered by the KPI
      dashboards, detail tools and `get_connections()`
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

# Oracle DBA Pack

* [ ] Initial implementation

---

# ClickHouse DBA Pack

* [ ] Initial implementation

---

# SQL Server DBA Pack

* [ ] Initial implementation

---

# MySQL DBA Pack

* [x] Covered by `packs/mysql-dba` (13 tools on MySQL 8)

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

* [x] Dockerfile (multi-stage, uv builder, non-root runtime)
* [x] Docker Compose example (`docker-compose.yaml`: PostgreSQL + `blueprint`
      server over Streamable HTTP with health checks)
* [x] Streamable HTTP example
* [ ] Health endpoint (the compose stack uses a TCP healthcheck; a dedicated
      HTTP endpoint is still open)

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
* [ ] GUI for "programming" packs: a visual editor to author and configure
      packs (tool YAML + SQL) and to monitor/control them at runtime
      (tool usage, health, results) — useful both for configuration and
      for control
* [x] Metrics endpoint
* [x] Prometheus integration
* [ ] NoSQL adapters
* [ ] Per-server environment label (e.g. `server.label: "docker-demo"`)
      embedded in every tool description, so agents can tell which
      database a server targets even when several Blueprint servers expose
      the same tool names (tool-name prefixing already disambiguates in
      clients that prefix server names)

---

# Long-term Vision

The objective is not simply to create another MCP server.

The objective is to establish a reusable architecture for building domain-oriented MCP servers.

Developers should spend their time defining **tools**, **SQL**, and **business concepts**, while the framework handles infrastructure, transport, validation, caching, formatting, and database abstraction.

Ultimately, adding a new tool should require little more than creating:

* one YAML definition
* one SQL file

without writing additional Python code.
