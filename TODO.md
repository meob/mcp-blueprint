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
* [ ] Every tool SQL enforces an `ORDER BY` (most significant rows first)
      and a `LIMIT` to bound result size (`get_largest_objects` already
      complies; audit the rest)

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
* [ ] Check against injection, parameters, unlimited queries

---

# Configuration

* [x] server.yaml
* [x] database.yaml
* [x] logging.yaml
* [x] pack.yaml

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
* [x] First tools with real parameters: `get_largest_objects` accepts an
      optional `object_name` LIKE filter on both reference DBA packs
* [x] Parameterized SQL escapes literal `%` as `%%` (documented in
      `docs/pack_development.md`) and the pipeline binds only non-`None`
      parameters

---

# Reference DBA Packs

More specialized administration packs.  The reference implementations are two
independent, single-engine packs that expose the same 12 tools:
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

* [x] Covered by `packs/mysql-dba` (12 tools on MySQL 8)

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
