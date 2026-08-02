# MCP Blueprint

**Build domain-oriented MCP servers without writing Python code for every project.**

MCP Blueprint is a lightweight framework for creating Model Context Protocol (MCP) servers from configuration files, SQL queries and metadata instead of custom application code.

Instead of exposing a generic SQL interface, MCP Blueprint exposes a curated set of business-oriented tools that are easier for LLMs to understand, safer to use and simpler to maintain.

---

## Why?

Many existing MCP database servers expose tools such as:

- execute_sql()
- query_database()

Although powerful, these tools require the LLM to:

- understand the database schema
- write efficient SQL
- know relationships between tables
- respect business rules
- avoid expensive queries

This approach works well for experiments but is often unsuitable for production environments.

MCP Blueprint follows a different philosophy:

> Don't expose the database.
> Expose the domain.

The LLM should ask for information, not write SQL.

---

## Example

Instead of

```
execute_sql(...)
```

an application exposes

```
get_customer()
get_customer_orders()
get_customer_payments()
search_customer()
```

or, for database administration,

```
get_operational_kpis()
get_performance_kpis()
get_security_kpis()
get_users()
get_database_sizes()
get_replication_status()
```

Every tool has a well-defined purpose and hides all SQL complexity.

---

# Architecture

```
                 +----------------+
                 |    LLM Agent   |
                 +--------+-------+
                          |
                     MCP Protocol
                          |
                  +-------+-------+
                  | MCP Blueprint |
                  +-------+--------+
                          |
          +---------------+----------------+
          |               |                |
      Tool Metadata     SQL Loader    Auth/Logging
          |               |
          +-------+-------+
                  |
           Relational Database
```

The framework is responsible for

- creating MCP tools
- parameter validation
- database connections
- logging
- error handling
- optional caching
- optional authorization

Application developers only provide configuration files.

---

# Philosophy

An MCP server should look like a REST API, not like a SQL console.

Each tool should represent a meaningful operation.

Good examples

```
get_customer()
search_customer()
get_invoice()
get_database_size()
```

Bad examples

```
execute_sql()
run_query()
```

---

# Project structure

```
mcp-blueprint/

    blueprint/

    config/

    packs/

    docs/

    examples/

    tests/
```

A pack contains everything needed for a specific domain.

Example:

```
packs/

    pg-dba/

        tools/

        sql/

        pack.yaml

    mysql-dba/

    sakila/

    customer/

    warehouse/
```

The engine is declared once per pack in `pack.yaml` (e.g.
`engines: [postgresql]`); packs that do not match the configured engine are
skipped, so `database.engine` selects both the adapter and the loaded packs.
A tool may still override per-engine via a `sql` map for packs that share a
tool across engines.  `template/pack` provides a minimal skeleton for authoring
new packs and is not auto-loaded.

---

# Tool definition

Every tool is described using YAML.

Example

```yaml
name: get_connections

description: Return connected sessions.

parameters:

  database:
    type: string
    required: false

sql:
  postgresql: sql/postgresql/get_connections.sql
```

No Python code should be required to create a new tool.

---

# SQL files

SQL remains external.

```
sql/

    postgresql/

        get_users.sql

        get_database_sizes.sql

        get_replication_status.sql
```

Changing database version or optimizer hints should never require changing Python code.

---

# Packs

A pack is a reusable collection of tools.

Examples

- PostgreSQL DBA Pack
- MySQL DBA Pack
- Oracle DBA Pack
- Customer Pack
- Sales Pack
- Warehouse Pack
- ERP Pack

Every pack is independent.

---

# Reference packs

The reference implementations are two independent administration packs with
the **same 12 tools**: `packs/pg-dba` (PostgreSQL 14+) and `packs/mysql-dba`
(MySQL 8+).  Each is single-engine (`engines: [postgresql]` / `engines: [mysql]`
in `pack.yaml`), self-contained and can evolve independently with engine-specific
tools.

With `database.engine: postgresql` only `pg-dba` loads; with
`database.engine: mysql` only `mysql-dba` loads.

Each pack contains ready-to-use tools for database administration, split into
KPI dashboards and detail tools.

KPI dashboards always return rows with a `status` of `ok`/`warning`/`error`:

- operational KPIs (connection slots, transaction wrap, database growth)
- performance KPIs (cache hit ratio, replication lag, index usage)
- security KPIs (pending SSL, roles with login, password checks)

Detail tools:

- users and roles
- database sizes
- database version
- largest objects
- replication status
- tuning configuration
- slow queries
- maintenance status
- index health

The packs do not expose SQL execution.

Only curated DBA operations.  All tools work with least-privilege monitoring
users (e.g. the `pg_monitor` role on PostgreSQL).

---

# Template pack

`template/pack` is the minimal skeleton for a new pack (pack metadata, one
example tool, one example SQL query).  It is not auto-loaded by the framework.
To start a new domain pack, copy the template or an existing pack such as
`packs/pg-dba` and replace tool names, descriptions and SQL.  See
`template/README.md`.

---

# Cross-database philosophy

Different database engines expose different system catalogs.

However, most administration concepts are identical.

Examples include

- connected sessions
- active sessions
- blocking chains
- locks
- storage usage
- fragmentation
- expensive queries
- replication
- transaction activity

Only SQL changes.

Tool names remain identical.

This allows an LLM to work with PostgreSQL, Oracle, or MySQL using exactly the same MCP interface.

---

# Design goals

- Configuration-driven
- Database-independent
- Domain-oriented
- Easy to extend
- Safe by default
- Small number of meaningful tools
- SQL separated from Python
- Production-ready

---

# Long-term vision

MCP Blueprint aims to become for MCP what REST frameworks became for HTTP APIs.

Developers should focus on describing their domain, not implementing infrastructure.

An MCP server should be assembled from reusable packs rather than developed from scratch.