# MCP Blueprint

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

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
get_performance_kpis()
get_users()
get_database_sizes()
get_replication_status()
```

Every tool has a well-defined purpose and hides all SQL complexity.

---

## Getting started

Install the framework and run the reference server:

```bash
uv sync --all-extras --dev
uv run blueprint serve --config config --transport stdio
```

Or run it in Docker with a bundled PostgreSQL over Streamable HTTP:

```bash
docker compose up --build
```

The server is then available at `http://localhost:8000/mcp`.

For a full walkthrough see [docs/installation.md](docs/installation.md),
[docs/quickstart.md](docs/quickstart.md) and
[docs/docker.md](docs/docker.md).

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

Beyond the tool API, MCP Blueprint owns the operational concerns — SQL safety
(read-only by default, explicit opt-in for writes, injection-proof
parameters), structured logging and telemetry — so pack authors never have to
implement them; see the [security model](docs/pack_development.md#security-model),
[logging, audit and tracing](docs/logging.md) and
[Prometheus metrics](docs/metrics.md).

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
    Dockerfile
    docker-compose.yaml
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
name: get_largest_objects
description: Return the largest tables and indexes by size, ordered descending.
sql: ../sql/get_largest_objects.sql
```

No Python code should be required to create a new tool.

---

# SQL files

SQL remains external.

```
sql/
        get_users.sql
        get_database_sizes.sql
        get_largest_objects.sql
```

Changing the database version or rewriting a query should never require changing Python code.

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

# Template pack

`template/pack` is the minimal skeleton for a new pack (pack metadata, one
example tool, one example SQL query).  It is not auto-loaded by the framework.
To start a new domain pack, copy the template or an existing pack such as
`packs/sakila` and replace tool names, descriptions and SQL.  See
`template/README.md`.

---

# Example pack: Sakila

`packs/sakila` is the recommended first example: a small, domain-oriented pack
for the [Sakila sample database](https://dev.mysql.com/doc/sakila/en/) on
PostgreSQL.  It lets an agent run a DVD rental store chatbot — recommend
films, inspect a film in detail and review a customer's rental activity —
without ever writing SQL.

| Tool                   | Purpose                                            |
| ---------------------- | -------------------------------------------------- |
| `search_films`         | Recommend films by optional title, category, rating. |
| `get_film`             | Full catalog record for one film.                  |
| `search_customer`      | Find a customer by first or last name.             |
| `get_customer_rentals` | Rental history with an active/overdue/returned status. |

Domain knowledge lives in SQL, not Python: `search_films` translates MPAA
rating codes into a human-readable `rating_label` and a numeric `min_age`,
and `get_customer_rentals` computes the rental `status`.  The tool
descriptions steer the agent, e.g. `search_customer` points at
`get_customer_rentals` to check a customer's situation.  See
[docs/sakila.md](docs/sakila.md) for the full walkthrough.

The DBA packs below are more specialized administration packs; study Sakila
first to see how a domain pack is built.

---

# Reference packs

The reference implementations are independent administration packs with
the **same 13 tools**: `packs/pg-dba` (PostgreSQL 14+), `packs/mysql-dba`
(MySQL 8+), `packs/oracle-dba` (Oracle 12c+), `packs/clickhouse-dba`
(ClickHouse 23+), `packs/sqlserver-dba` (SQL Server 2016+) and
`packs/mariadb-dba` (MariaDB 10.4+).  Each is self-contained and can evolve
independently with engine-specific tools.

With `database.engine: postgresql` the `pg-dba` and `sakila` packs load; with
`database.engine: mysql` only `mysql-dba` loads; with
`oracle`, `clickhouse`, `sqlserver` or `mariadb` the matching `*-dba` pack
loads.  The engine aliases `postgres`, `mssql` and `sql_server` are also
accepted.

The four additional engines are optional: install their drivers through the
extras `uv sync --extra oracle`, `--extra clickhouse`, `--extra sqlserver`
(or `--all-extras`) and bring a database up with
`docker compose -f docker-compose.databases.yaml up -d`.

Each pack contains ready-to-use tools for database administration, split into
KPI dashboards and detail tools.

KPI dashboards always return rows with a `status` of `ok`/`warning`/`error`:

- operational KPIs (connection slots, transaction wrap, database growth)
- performance KPIs (cache hit ratio, replication lag, index usage)
- security KPIs (pending SSL, roles with login, password checks)

Detail tools:

- users and roles
- active sessions and connections
- database sizes
- database version
- largest objects
- replication status
- tuning configuration
- slow queries
- maintenance status
- index health

The packs do not expose SQL execution.

Only curated DBA operations.  All tools can work with least-privilege monitoring
users (e.g. the `pg_monitor` role on PostgreSQL).

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

---

# License

Released under the [Apache License 2.0](LICENSE).
