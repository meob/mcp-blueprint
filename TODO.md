# TODO

Implementation backlog for **MCP Blueprint**.  The project is near maturity: the
core framework, all six reference DBA packs and the Sakila example are done.
This document summarizes what is in place and tracks only the remaining work.

The detailed history is archived in `staff/TODO_old.md`.

---

# Done

## Core framework

- Configuration-driven server: YAML config (`server`, `database`, `logging`,
  `metrics`, `pack`), environment expansion, Jinja2 templates, parameter
  validation, structured logging, error handling.
- FastMCP integration: automatic tool registration, parameter conversion,
  docstring generation, JSON responses.
- Transports: stdio and Streamable HTTP (configurable per server).
- Async-first architecture with connection pooling.

## Database adapters

- Six engines behind one `DatabaseAdapter` interface: PostgreSQL (psycopg3),
  MySQL (asyncmy), Oracle (oracledb thin), ClickHouse (clickhouse-driver),
  SQL Server (pyodbc) and MariaDB (subclass of the MySQL adapter).
- Engine-aware pack loading: engine declared in `pack.yaml`, optional
  per-tool `sql` map for multi-engine tools; aliases `postgres`, `mssql`,
  `sql_server` accepted.

## Packs

- Reference DBA packs exposing the same 13 tools each: `pg-dba`,
  `mysql-dba`, `oracle-dba`, `clickhouse-dba`, `sqlserver-dba`,
  `mariadb-dba`.  KPI dashboards (operational/performance/security, status
  `ok`/`warning`/`error`) plus detail tools (users, connections, sizes,
  version, largest objects, replication, tuning, slow queries, maintenance,
  index health).
- `packs/sakila`: canonical domain-oriented example (customer account,
  film recommendations, per-store stock) on PostgreSQL.
- Sizes (`size_bytes`) are reported as raw byte counts across all engines:
  no engine-specific human-readable `size`/`size_mb` strings (databases,
  tables, indexes).
- `template/pack`: minimal skeleton, not auto-loaded.

## Security

- Read-only by default: SQL guard accepts exactly one `SELECT` (or
  `WITH`/`WITH RECURSIVE` ending in `SELECT`), checked at load time and at
  runtime; fail-closed.
- Writes require explicit `writes: true` in the tool YAML.
- Injection hardening: `{{ }}` interpolation rejected, values only as bound
  placeholders.
- Result row cap `server.max_rows` (default `1000`).

## Agent guidance

- Pack-level `instructions` appended to every tool description; global usage
  notice; server-level `instructions` for clients that surface them.
- Standalone `get_replication_status` reports `NULL` lag instead of a
  misleading `0`.

## Observability

- Structured JSON logging, rotating file handler, per-call `trace_id`,
  sensitive-data redaction, optional audit channel.
- Optional Prometheus metrics endpoint (disabled by default, works with
  stdio).

## Tooling and tests

- Unit suites plus live integration tests (skipped when an engine is
  unreachable); SQL conformance suite (13 tools/pack, guard, placeholders).
- Least-privilege monitoring users validated on PostgreSQL and MySQL.
- GitHub Actions CI (`ci.yml`): lint/typecheck, unit tests, and live
  integration tests against all six engines, reusing the provided compose
  stacks (`.github` workflow, `docker-compose.ci.yaml` host-port override).

## Docker

- Multi-stage `Dockerfile`; `docker-compose.yaml` (PostgreSQL + Blueprint over
  Streamable HTTP); `docker-compose.databases.yaml` provisioning the
  containerized databases — MySQL 8 (`3308`), Oracle Free 23 (`1521`),
  ClickHouse 24.8 (`9000`/`8123`), SQL Server 2022 (`1433`) and MariaDB 11.4
  (`3307`) — with first-boot least-privilege grants (`docker/init/`) and
  Sakila data for MySQL/MariaDB.

---

# Open

## Transport

- Test stdio with OpenCode (done: the `pg-dba` server answers `get_connections`
  and `get_database_version` from OpenCode).
- [ ] Test stdio with Claude Desktop.
- [ ] Test stdio with Gemini CLI.
- [ ] Dedicated HTTP health endpoint (the compose stack uses a TCP healthcheck
      for now).

## Database layer

- [ ] Transaction management in the generic adapter.

## Formatting

- [ ] Duration formatting.
- [ ] Computed columns.

## Cache

- [ ] aiocache backend.
- [ ] Cache invalidation.

## Security

- [ ] Authentication hooks (future).

## Observability

- [ ] OpenTelemetry exporter as an optional extra.

## Documentation

- [ ] Adapter development guide.
- [ ] Contribution guide.

## Examples

- [ ] Oracle example.
- [ ] ERP Pack example.

---

# Future features

## Workflow tools

Higher-level tools orchestrating atomic tools:

- [ ] `diagnose_performance()`, `diagnose_storage()`, `diagnose_autovacuum()`,
      `diagnose_replication()`.

## AI-assisted features

- [ ] Tool self-documentation.
- [ ] Automatic OpenAPI-like documentation.
- [ ] Tool usage statistics.

## Paper benchmark (Sakila / Model Demotion)

Validate the illustrative figures used in `staff/mcp-blueprint_zenodo.md`
(Section 6).  The ~4,200 token, ~350 token, failure-rate and "100%
correctness" numbers are hypotheses to be tested, not measurements.

- [ ] Define the benchmark protocol: fixed prompt set for the Sakila rental
      workflow (`customer_account_summary` → `recommend_films`),
      model tiers (e.g. large/medium/SLM), temperature 0, repeated runs.
- [ ] Record inputs and outputs (tool invocations, tool results, final answer)
      to a log directory.
- [ ] Collect metrics per tier: prompt/response tokens, latency, cost,
      correctness and failure rate.
- [ ] Report results in the paper and replace the illustrative figures.

## Nice to have

- [ ] Plugin system.
- [ ] Pack installer / pack repository.
- [ ] Web administration UI.
- [ ] Visual pack editor (author YAML + SQL and monitor at runtime).
- [ ] NoSQL adapters.
- [ ] Per-server environment label (`server.label`) embedded in tool
      descriptions so agents can tell which database a server targets.

---

# Long-term vision

MCP Blueprint aims to be to MCP what REST frameworks became to HTTP APIs:
developers describe **tools**, **SQL** and **business concepts**, while the
framework handles infrastructure, transport, validation, caching, formatting
and database abstraction.  Adding a tool should require little more than one
YAML definition and one SQL file.
