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

The first pack is the PostgreSQL DBA Pack.

### Rationale

It demonstrates all major framework capabilities while providing immediate practical value.

The same architectural model can later be applied to Oracle, MySQL and business-oriented domains.

---

# Guiding Principle

Every architectural decision should support the same long-term objective:

> Allow developers to describe **what** a tool does, while the framework manages **how** it is exposed, executed and maintained.
