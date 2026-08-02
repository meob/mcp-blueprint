# DECISIONS

This document records the architectural decisions made during the design of **MCP Blueprint**.

Its purpose is to explain **why** specific decisions were made, reducing the risk of revisiting the same discussions or unintentionally introducing architectural regressions.

---

# Decision 1

## MCP servers expose domains, not databases

### Decision

MCP Blueprint exposes domain-oriented tools rather than generic SQL execution.

Examples:

* get_customer()
* get_connections()
* get_database_size()

instead of:

* execute_sql()
* run_query()

### Rationale

LLMs should decide **what information is needed**, not **how to retrieve it**.

Encapsulating SQL provides:

* better security
* better performance
* stable interfaces
* easier maintenance
* simpler prompts

---

# Decision 2

## SQL remains external

### Decision

SQL is always stored in dedicated files.

Python code never embeds SQL statements.

### Rationale

This allows:

* easier maintenance
* DBA-friendly editing
* database-specific optimization
* version-specific SQL
* cleaner Python code

---

# Decision 3

## YAML is the primary configuration format

### Decision

Tool definitions and configuration are written in YAML.

### Rationale

YAML is:

* readable
* concise
* easy to edit
* widely adopted

The goal is to make adding new tools possible without writing Python code.

---

# Decision 4

## Python is the implementation language

### Decision

Python is the reference implementation language.

### Rationale

Reasons include:

* mature MCP ecosystem
* FastMCP support
* excellent async support
* broad database driver availability
* strong AI tooling support

---

# Decision 5

## FastMCP is the reference MCP implementation

### Decision

FastMCP is used as the underlying MCP framework.

### Rationale

FastMCP provides a clean and productive API while remaining an implementation detail hidden by the framework.

Packs should remain independent from the underlying MCP library.

---

# Decision 6

## Support both stdio and Streamable HTTP

### Decision

Both transports are first-class citizens.

### Rationale

stdio is ideal for:

* local development
* desktop clients
* coding assistants

Streamable HTTP is better suited for:

* production
* containers
* Kubernetes
* authentication
* reverse proxies

Changing transport should never require changing packs.

---

# Decision 7

## Async-first architecture

### Decision

The framework is designed around Python asyncio.

### Rationale

Benefits include:

* improved scalability
* efficient connection pooling
* concurrent execution
* future workflow support

---

# Decision 8

## Database abstraction

### Decision

Database-specific code is isolated behind adapters.

### Rationale

The framework should remain independent from the underlying DBMS.

Only adapters and SQL should change.

---

# Decision 9

## One semantic interface across databases

### Decision

Equivalent concepts should expose identical tool names across supported relational databases.

Example:

* PostgreSQL
* MySQL
* Oracle
* ClickHouse


all expose:

* get_connections()
* get_blocking_sessions()
* get_database_size()

### Rationale

Different DBMS implementations expose different catalogs but represent the same operational concepts.

Using a common semantic interface allows LLMs to work across multiple database engines without changing prompts.

---

# Decision 10

## Packs contain domain knowledge

### Decision

A pack contains:

* tool definitions
* SQL
* configuration
* optional formatting

The framework contains infrastructure.

### Rationale

This separation keeps packs lightweight and reusable.

---

# Decision 11

## Lightweight cache

### Decision

The framework uses an in-memory cache.

Redis is not required.

### Rationale

Most MCP deployments do not require distributed caching.

A lightweight cache is simpler to configure and sufficient for the expected workloads.

---

# Decision 12

## Configuration-driven development

### Decision

The preferred way to extend the framework is through configuration rather than Python code.

### Rationale

The long-term objective is that adding a new tool requires little more than:

* one YAML definition
* one SQL file

without modifying the framework itself.

---

# Decision 13

## Reference implementation

### Decision

The first packs are the reference DBA packs: `packs/pg-dba` (PostgreSQL) and
`packs/mysql-dba` (MySQL).

### Rationale

It demonstrates all major framework capabilities while providing immediate practical value.

The same architectural model can later be applied to Oracle, MySQL and business-oriented domains.

---

# Decision 14

## Packs are engine-aware

### Decision

The engine is declared once at pack level in `pack.yaml` (e.g.
`engines: [postgresql]`); packs that do not match the configured engine are
skipped at load time.  When `engines` is absent the pack is engine-agnostic.
A tool may still override per-tool, via a `sql` map keyed by engine or a shared
`sql` path with an `engines` list, for packs that genuinely share a tool across
engines.

### Rationale

Declaring the engine once per pack keeps the common case (one pack, one
engine) simple, while the tool-level override remains available for future
multi-engine packs.  The configured engine (`database.engine`) selects both
the adapter and the packs that contribute tools, so loading is deterministic
and dialect errors are prevented by construction.  The agent still sees a
stable tool interface regardless of the underlying database.

---

# Decision 15

## Template and pack are distinct objects

### Decision

`template/pack` is a minimal skeleton (pack metadata, one example tool, one
example SQL file) and is **not** auto-loaded by the framework.  Concrete packs
live in `packs/` (e.g. `packs/pg-dba`).

### Rationale

A new domain pack (e.g. a "Sakila" pack) can be created by copying the template
or an existing pack and touching only names, descriptions and SQL queries.
Keeping the template free of domain content makes it stable and reusable.

---

# Decision 16

## KPI-based reference packs

### Decision

`packs/pg-dba` and `packs/mysql-dba` expose the same three KPI dashboards
(operational, performance, security) that always return rows with a `status`
of `ok`/`warning`/`error`, plus the same detail tools (users, largest objects,
slow queries, index health).  They are two independent, single-engine packs:
PostgreSQL 14+ and MySQL 8+.

### Rationale

KPI rows with a computed `status` give the agent an immediate diagnosis and
reduce round-trips.  The reference packs are deliberately separate and
single-engine so they can evolve independently (PostgreSQL-only and
MySQL-only tools) and act as complete, copyable examples of a Blueprint
customization.  Both are validated with least-privilege monitoring users,
proving the engine-aware loading: the same 11 tool names are exposed on both
engines by two distinct packs.

PostgreSQL 12 and 13 reached end-of-life and several relevant columns (e.g.
`total_exec_time` in `pg_stat_statements`) were renamed in PostgreSQL 14;
older versions would require version-forked SQL that a single static statement
cannot express.

---

# Guiding Principle

Every architectural decision should support the same long-term objective:

> Allow developers to describe **what** a tool does, while the framework manages **how** it is exposed, executed and maintained.
