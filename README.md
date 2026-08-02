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

    dba/

        tools/

        sql/
            postgresql/

        config/

    sakila/

    customer/

    warehouse/
```

Tools declare the engines they support: a per-engine `sql` map (or a shared
`sql` path with an `engines` list).  Only the tools that can run on the
configured engine are loaded.  `template/pack` provides a minimal skeleton for
authoring new packs and is not auto-loaded.

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

# DBA Pack

The first reference implementation is the **DBA pack** (`packs/dba`, formerly
`packs/pg-dba`), a cross-database administration pack supporting
**PostgreSQL 14+** and **MySQL 8+**.  Each tool ships one SQL file per engine
under `sql/postgresql/` and `sql/mysql/`; the tool interface is identical on
both engines.

It contains ready-to-use tools for database administration, split into KPI
dashboards and detail tools.

KPI dashboards always return rows with a `status` of `ok`/`warning`/`error`:

- operational KPIs (connection slots, transaction wrap, database growth)
- performance KPIs (cache hit ratio, replication lag, index usage)
- security KPIs (pending SSL, roles with login, password checks)

Detail tools:

- users and roles
- database sizes
- largest objects
- replication status
- tuning configuration
- slow queries
- maintenance status
- index health

The pack does not expose SQL execution.

Only curated DBA operations.  All tools work with least-privilege monitoring
users (e.g. the `pg_monitor` role on PostgreSQL).

---

# Template pack

`template/pack` is the minimal skeleton for a new pack (pack metadata, one
example tool, one example SQL query).  It is not auto-loaded by the framework.
To start a new domain pack, copy the template or an existing pack such as
`packs/dba` and replace tool names, descriptions and SQL.  See
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