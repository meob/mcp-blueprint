# Architecture

## Overview

MCP Blueprint is designed as a **framework** for building domain-oriented MCP servers rather than database-specific MCP servers.

The framework is responsible for all infrastructure concerns, while application developers only define tools, SQL queries and configuration files.

The primary design principle is:

> **Expose the domain, not the database.**

An LLM should decide **which information is needed**, not **how to retrieve it**.

---

# Technology Stack

| Component         | Choice                  | Notes                                                            |
| ----------------- | ----------------------- | ---------------------------------------------------------------- |
| Language          | Python 3.12+            | Modern async support and excellent MCP ecosystem                 |
| MCP Framework     | FastMCP                 | Clean API and currently the best choice for Python-based servers |
| Validation        | Pydantic                | Tool parameters and configuration validation                     |
| Configuration     | YAML                    | Human-readable and version-control friendly                      |
| SQL Templates     | Jinja2                  | Optional conditional SQL generation                              |
| PostgreSQL Driver | psycopg3                | Modern PostgreSQL driver                                         |
| MySQL Driver      | asyncmy                 | Async MySQL 8 driver                                             |
| Other Drivers     | Adapter-based           | Oracle, MariaDB, ClickHouse, ... (planned)                       |
| Logging           | structlog               | Structured logs suitable for production                          |
| Cache             | cachetools or aiocache  | Lightweight in-memory cache                                      |
| Transport         | stdio + Streamable HTTP | Same codebase supports both                                      |

---

# High-Level Architecture

```
                     +----------------------+
                     |      LLM Agent       |
                     +----------+-----------+
                                |
                           MCP Protocol
                                |
                    +-----------+-----------+
                    |      FastMCP Layer    |
                    +-----------+-----------+
                                |
                      Tool Registration Layer
                                |
                 +--------------+--------------+
                 |                             |
            Tool Metadata                 SQL Loader
                 |                             |
                 +--------------+--------------+
                                |
                      Parameter Validation
                                |
                         SQL Rendering
                                |
                       Database Adapter
                                |
                  +------+------+------+------+
                  |             |             |
             PostgreSQL      Oracle         MySQL
                  |
             Query Execution
                  |
            Result Formatter
                  |
                Cache
                  |
            JSON Response
```

---

# Design Philosophy

The framework should contain all infrastructure code.

A pack should contain only:

* configuration
* SQL
* metadata
* optional formatting rules

Adding a new tool should not require writing Python code.

---

# Domain-Oriented Tools

A tool represents a business or operational concept rather than a SQL statement.

Good examples:

* get_customer()
* search_customer()
* get_invoice()
* get_connections()
* get_database_size()
* get_blocking_sessions()

Bad examples:

* execute_sql()
* run_query()
* query_database()

The framework intentionally discourages generic SQL execution.

---

# Tool Lifecycle

Every tool follows the same execution pipeline.

```
YAML Definition

        ↓

Parameter Validation

        ↓

SQL Template Rendering

        ↓

Database Execution

        ↓

Optional Post-processing

        ↓

Cache

        ↓

JSON Response
```

Each stage should be independent and replaceable.

---

# Transport Layer

The framework should support both MCP transports.

## stdio

Recommended for:

* Claude Desktop
* OpenCode
* Gemini CLI
* Cursor
* Local development

Advantages:

* Zero configuration
* Simple debugging
* No networking required

## Streamable HTTP

Recommended for:

* Docker deployments
* Kubernetes
* Reverse proxies
* Authentication
* TLS
* Enterprise environments

Both transports must use exactly the same internal code.

Changing transport should never require changing packs.

---

# Async Architecture

The framework should be fully asynchronous.

Reasons:

* Better scalability
* Efficient connection pooling
* Multiple database requests can execute concurrently
* Better support for future workflow tools

The implementation should rely on Python asyncio.

---

# Database Abstraction

The framework should never depend directly on a specific database.

Instead, all engines implement a common interface.

```
DatabaseAdapter

    engine          # canonical identifier, e.g. "postgresql"

    execute(sql, parameters)

    test_connection()
```

Possible implementations:

* PostgreSQL (implemented)
* MySQL (implemented)
* Oracle
* MariaDB
* SQLite
* ClickHouse
* SQL Server

Only SQL changes.

The framework remains unchanged.
Could be applied to NoSQL database too, SQL is replaced by queries in the required language.

---

# Engine-Aware Pack Loading

The engine is declared once, at pack level, in `pack.yaml`:

```yaml
# packs/pg-dba/pack.yaml
name: pg-dba
engines: [postgresql]
```

When `engines` is absent the pack is engine-agnostic and loads on every engine.
Packs whose declared engines do not match the configured engine (from
`database.engine`) are skipped at registration time.  The configured engine
therefore selects both the database adapter and the packs that contribute
tools.

A tool may still restrict or map engines per-tool, overriding the pack default,
when a single pack genuinely shares a tool across engines:

* `sql` as a **map keyed by engine**: the tool exists for an engine only when
  it has a SQL entry for it:

  ```yaml
  sql:
    postgresql: ../sql/postgresql/get_users.sql
    mysql:      ../sql/mysql/get_users.sql
  ```

* a single shared `sql` path restricted with an explicit `engines` list:

  ```yaml
  engines: [postgresql]
  sql: ../sql/get_vacuum_status.sql
  ```

The reference packs keep the common case simple: each is single-engine, so its
tools use a plain `sql` path and the pack-level `engines` decides availability.

The reference packs are `packs/pg-dba` (PostgreSQL 14+) and `packs/mysql-dba`
(MySQL 8+).  They expose the same 12 tool names and are developed independently:
each is a complete, copyable example of a Blueprint customization.

---

# SQL Management

SQL is always external.

A single-engine pack stores one SQL file per tool in its own `sql/` directory:

```
packs/pg-dba/sql/

    get_connections.sql
    get_database_size.sql
    get_blocking_sessions.sql
```

Tools point at their SQL file:

```yaml
sql: ../sql/get_connections.sql
```

A multi-engine pack stores one SQL file per engine and maps per-tool:

```
packs/audit/sql/

    postgresql/
        get_users.sql

    mysql/
        get_users.sql
```

```yaml
sql:
  postgresql: ../sql/postgresql/get_users.sql
```

Benefits:

* Easier maintenance
* Database-specific optimizations
* Version-specific SQL
* DBA-friendly editing

Python code should never contain embedded SQL.

---

# SQL Templates

Jinja2 templates may be used when optional filtering is required.

Example:

```sql
SELECT *
FROM pg_stat_activity

{% if database %}
WHERE datname = %(database)s
{% endif %}
```

This avoids maintaining multiple nearly identical SQL files.

---

# Tool Metadata

Each tool is described by a YAML file.

Example:

```yaml
name: get_connections

description: Return active database sessions.

parameters:

  database:
    type: string
    required: false

sql:
  postgresql: ../sql/postgresql/get_connections.sql

cache:
  ttl: 30
```

The framework loads and registers tools automatically.

---

# KPI-Based Tools

Diagnostic packs (e.g. `packs/pg-dba` and `packs/mysql-dba`) expose KPI
dashboards rather than raw catalog listings.  A KPI tool always returns rows
with the shape:

```yaml
kpi_name: connection_slots_used
current_value: 47
unit: percent
suggested_threshold: 90
status: ok            # ok | warning | error
```

`status` is computed from `current_value` against `suggested_threshold`, so an
agent gets an immediate diagnosis without parsing raw numbers.  Detail tools
(user listings, largest objects, slow queries) complement the dashboards.

---

# Template vs Pack

`template/pack` contains the minimal skeleton needed to author a new pack:

```
template/pack/
    pack.yaml
    tools/
    sql/
```

It is **not** auto-loaded by the framework.  A concrete pack (e.g.
`packs/pg-dba`) is created by copying the template and filling in tool names,
descriptions and SQL queries.  The separation keeps the template free of
domain content while packs remain self-contained and installable.

---

# Result Formatting

Raw SQL results are rarely ideal for LLM consumption.

Optional formatting may include:

* column renaming
* byte → MB/GB conversion
* timestamp formatting
* duration formatting
* derived fields
* removal of internal columns
* URL generation

Formatting should be implemented as reusable components.

---

# Cache

The framework uses a lightweight in-memory cache.

Redis is intentionally not required.

Suggested implementations:

* cachetools
* aiocache

Each tool declares its own cache policy.

Examples:

```
Database version

TTL = infinite
```

```
Database size

TTL = 30 seconds
```

```
Connected sessions

TTL = 5 seconds
```

The cache is optional and completely transparent.

---

# Connection Management

Each adapter manages its own connection pool.

For PostgreSQL:

* psycopg3
* async connections
* configurable pool size

Connections should never be created for every request.

---

# Configuration

Everything should be configurable through YAML.

Example:

```
config/

    server.yaml

    database.yaml

    logging.yaml
```

Configuration should not require Python modifications.

---

# Logging

Structured logging is preferred.

Suggested library:

* structlog

Logs should support production environments and centralized log collection.

---

# Security

The framework should support tool-level security.

Possible metadata:

```yaml
roles:

  - dba

  - readonly
```

Optional attributes:

```yaml
enabled: false
```

```yaml
requires_confirmation: true
```

The framework should make future authentication mechanisms easy to integrate.

---

# Packs

A pack is a reusable collection of tools.

Typical contents:

```
pack/

    config/

    sql/

    tools/

    formatters/
```

Packs are independent and installable.

Examples:

* PostgreSQL DBA Pack
* Oracle DBA Pack
* SQL Server DBA Pack
* Customer Pack
* ERP Pack

---

# Cross-Database Strategy

Although relational databases expose different system catalogs, most administration concepts are identical.

Examples include:

* connected sessions
* active sessions
* blocking chains
* locks
* storage usage
* fragmentation
* expensive queries
* replication
* transaction activity

The framework should expose the same logical tools across all supported database engines.

Only SQL implementation changes.

This allows an LLM to use exactly the same MCP interface regardless of the underlying DBMS.

---

# Future Workflow Tools

The current focus is atomic tools.

Future versions may introduce workflow tools.

Example:

```
diagnose_performance()

    ↓

get_connections()

    ↓

get_wait_events()

    ↓

get_blocking_sessions()

    ↓

get_top_queries()
```

These tools orchestrate multiple atomic tools to provide higher-level diagnostics.

---

# Core Principle

The heart of MCP Blueprint is **not** FastMCP.

The core is the execution pipeline:

```
Tool Loader

        ↓

YAML Metadata

        ↓

Parameter Validation

        ↓

SQL Loader

        ↓

Jinja Rendering

        ↓

Database Adapter

        ↓

Formatter

        ↓

Cache

        ↓

JSON Response
```

Everything else is implementation detail.

The framework should make adding a new tool almost as simple as adding two files:

* one YAML definition
* one SQL query

No Python code should be required for standard use cases.
