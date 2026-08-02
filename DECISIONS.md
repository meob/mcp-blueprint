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

The first pack is the DBA pack (`packs/dba`, formerly `packs/pg-dba`), a cross-database administration pack.

### Rationale

It demonstrates all major framework capabilities while providing immediate practical value.

The same architectural model can later be applied to Oracle, MySQL and business-oriented domains.

---

# Decision 14

## Tools are engine-aware

### Decision

Each tool declares which engines it supports.  Two mechanisms, both optional:

* `sql` as a map keyed by engine (`postgresql`, `mysql`, `oracle`)
* a shared `sql` path restricted by an explicit `engines` list

Tools that cannot run on the configured engine (from `database.engine`) are
skipped at load time.

### Rationale

The same logical tool (replication, users, storage) needs different SQL per
DBMS.  Tagging tools by engine keeps one pack usable across engines while
preventing SQL dialect errors.  The agent still sees a stable interface
regardless of the underlying database.

---

# Decision 15

## Template and pack are distinct objects

### Decision

`template/pack` is a minimal skeleton (pack metadata, one example tool, one
example SQL file) and is **not** auto-loaded by the framework.  Concrete packs
live in `packs/` (e.g. `packs/dba`).

### Rationale

A new domain pack (e.g. a "Sakila" pack) can be created by copying the template
or an existing pack and touching only names, descriptions and SQL queries.
Keeping the template free of domain content makes it stable and reusable.

---

# Decision 16

## KPI-based pack tools, minimum PostgreSQL 14

### Decision

The `dba` pack exposes three KPI dashboards (operational, performance,
security) that always return rows with a `status` of `ok`/`warning`/`error`,
plus detail tools (users, largest objects, slow queries, index health).
Supported engines: PostgreSQL 14+ and MySQL 8+.

### Rationale

KPI rows with a computed `status` give the agent an immediate diagnosis and
reduce round-trips.  The framework is validated against PostgreSQL 14+ and
MySQL 8+ (both with least-privilege monitoring users), proving the
engine-aware tool loading: the same YAML pack exposes the same tool names on
both engines, with only the SQL file changing.

PostgreSQL 12 and 13 reached end-of-life and several relevant columns (e.g.
`total_exec_time` in `pg_stat_statements`) were renamed in PostgreSQL 14;
older versions would require version-forked SQL that a single static statement
cannot express.

---

# Guiding Principle

Every architectural decision should support the same long-term objective:

> Allow developers to describe **what** a tool does, while the framework manages **how** it is exposed, executed and maintained.
