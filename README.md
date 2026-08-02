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

or, for PostgreSQL administration,

```
get_connections()
get_blocking_sessions()
get_wait_events()
get_database_size()
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

        config/

    customer/

    warehouse/
```

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

sql: sql/get_connections.sql
```

No Python code should be required to create a new tool.

---

# SQL files

SQL remains external.

```
sql/

    get_connections.sql

    get_wait_events.sql

    get_database_size.sql
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

# PostgreSQL DBA Pack

The first reference implementation is the PostgreSQL DBA Pack.

It contains ready-to-use tools for database administration.

Examples include

- connected sessions
- active sessions
- blocking sessions
- lock analysis
- wait events
- database size
- table size
- index bloat
- missing indexes
- replication
- WAL statistics
- autovacuum
- transaction ID usage
- longest running queries
- slow queries

The pack does not expose SQL execution.

Only curated DBA operations.

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