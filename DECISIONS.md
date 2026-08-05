# DECISIONS

Architectural decisions behind **MCP Blueprint**.  Each decision records *why*
a specific choice was made, to avoid revisiting settled discussions or
introducing regressions.  The complete historical record is archived in
`staff/DECISIONS_old.md`.

---

# D1 — MCP servers expose domains, not databases

MCP Blueprint exposes domain-oriented tools (`get_customer()`,
`get_connections()`, `get_database_size()`) instead of generic SQL execution
(`execute_sql()`, `run_query()`).

LLMs should decide **what** information is needed, not **how** to retrieve it.
Encapsulating SQL gives better security, stable interfaces and simpler prompts.

---

# D2 — SQL remains external

SQL always lives in dedicated files; Python never embeds statements.  This
keeps queries DBA-friendly, engine-specific and version-specific without
touching framework code.

---

# D3 — Configuration-driven development

Tools and servers are described in YAML.  The goal: adding a tool requires one
YAML definition and one SQL file, with no framework changes.  Python is the
reference implementation language (mature MCP ecosystem, async, broad driver
support).

---

# D4 — FastMCP is the reference MCP implementation

FastMCP provides the underlying transport and tool layer but stays an
implementation detail hidden by the framework: packs never depend on it.

---

# D5 — Both transports are first-class

stdio suits local development, desktop clients and coding assistants;
Streamable HTTP suits production, containers and reverse proxies.  Changing
transport never changes packs.

---

# D6 — Database code is isolated behind adapters

Each DBMS gets a `DatabaseAdapter` behind a common interface (PostgreSQL,
MySQL, Oracle, ClickHouse, SQL Server, MariaDB).  The framework is
DBMS-independent; only adapters and SQL change per engine.

---

# D7 — One semantic interface across databases

Equivalent concepts expose identical tool names across engines (the six `*-dba`
packs share the same 13 tools).  LLMs work across databases without changing
prompts, even though the underlying catalogs differ.

---

# D8 — Packs contain domain knowledge

A pack holds tool definitions, SQL and metadata; the framework owns
infrastructure.  Packs stay lightweight, reusable and independent of the MCP
library.

---

# D9 — Packs are engine-aware

The engine is declared once in `pack.yaml` (`engines: [postgresql]`); packs
that do not match `database.engine` are skipped, so the configured engine
selects both the adapter and the loaded packs.  A tool may override per-engine
via a `sql` map or a shared `sql` path with an `engines` list.  This keeps
loading deterministic and prevents dialect errors by construction.

---

# D10 — KPI-based reference packs

The DBA packs expose three KPI dashboards (operational, performance, security)
that always return rows with a `status` of `ok`/`warning`/`error`, plus the
same detail tools.  Computed status rows give the agent an immediate diagnosis
and reduce round-trips.  Packs are independent and single-engine so they can
evolve separately and act as complete, copyable examples.

PostgreSQL 12/13 are not supported: several `pg_stat_statements` columns were
renamed in 14, and a single static statement cannot fork per version.

---

# D11 — Security model

- Read-only by default: a SQL guard accepts exactly one `SELECT` (or
  `WITH`/`WITH RECURSIVE` ending in `SELECT`), enforced at load time and
  re-checked at runtime on the rendered statement; fail-closed.
- Writes require an explicit opt-in (`writes: true` in the tool YAML).
- Injection hardened: `{{ }}` interpolation rejected, values bound as
  placeholders only.
- Result rows capped by `server.max_rows` (default `1000`).
- All tools work with least-privilege monitoring users.

---

# D12 — Lightweight cache

An in-memory cache (cachetools) with per-tool TTL.  Redis is not required: most
MCP deployments do not need distributed caching.

---

# D13 — Optional extra engines

Oracle, ClickHouse, SQL Server and MariaDB ship as separate single-engine packs
with optional driver extras (`[oracle]`, `[clickhouse]`, `[sqlserver]`;
MariaDB reuses the MySQL adapter on asyncmy).  A `docker-compose.databases.yaml`
stack provisions all containerized databases with least-privilege monitoring
users for development and validation.

Two driver realities shaped the implementation:

- **clickhouse-driver removed its asyncio client** after 0.2.6, so the adapter
  wraps the synchronous `Client` in `asyncio.to_thread`.
- **Reserved words cannot be column aliases**: `user` and `size` break Oracle
  parsing, `user` and `schema` break SQL Server, so aliases are quoted
  (`AS "size"`, `AS [user]`) to keep identical output column names.

---

# D14 — Sizes are reported in bytes

The DBA packs return sizes (databases, tables, indexes) as raw byte counts in a
single `size_bytes` column, never as engine-specific human-readable strings.
Earlier versions used `pg_size_pretty()`, `formatReadableSize()` or string
conversions, so each engine returned a different `size`/`size_mb` format; an
agent should receive one comparable unit, and byte counts are exact and
lossless.

---

# Guiding principle

Every decision serves the same objective:

> Allow developers to describe **what** a tool does, while the framework
> manages **how** it is exposed, executed and maintained.

---

# D15 — The sakila pack encapsulates domain logic server-side

The canonical `sakila` pack ships domain tools that resolve entities and
assemble business answers server-side (`customer_account_summary`,
`recommend_films`, `film_stock`, `rental_history`, `search_customer`) rather
than thin, table-shaped lookups.

A benchmark comparing generic SQL, an early thin-tool pack and this pack on
the same 15 tasks and databases showed the thin-tool design was barely better
than generic SQL, while the verticalized design reached 0.996 mean accuracy
vs 0.711 (SQL) at a fraction of the tokens and latency.  The example pack
must demonstrate the framework's value proposition, so the verticalized
design is the one shipped.  The frozen early pack is preserved in the
benchmark repository (`packs_baseline/`) only for reproducibility of the
recorded results.
