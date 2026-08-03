# Pack development guide

A **pack** is a reusable collection of domain-oriented tools.  It contains only
configuration, SQL and metadata — no Python code.

## Pack layout

```
packs/
    my-pack/
        pack.yaml          # optional pack metadata
        tools/             # one YAML file per tool
        sql/               # one SQL file per query
```

## pack.yaml

```yaml
name: my-pack
version: 1.0.0
engines: [postgresql]
description: Describe the domain this pack covers.
```

| Field         | Type            | Description                                        |
| ------------- | --------------- | -------------------------------------------------- |
| `name`        | string          | Pack name.                                         |
| `version`     | string          | Pack version.                                      |
| `engines`     | list of strings | Optional; restricts the pack to these engines.     |
| `description` | string          | Short description of the pack domain.              |

When `engines` is present, the pack is loaded only if the configured engine
(`database.engine`) is listed.  When absent, the pack loads on every engine.
The pack manifest is optional: a pack without `pack.yaml` is engine-agnostic.

### Per-server pack allowlist

A server can restrict which packs it loads, on top of the engine filter, with
`server.packs` in `server.yaml` (a list of pack names).  When set, only packs
whose directory name is listed are loaded; when omitted (the default) all
engine-compatible packs load.  The value also accepts a comma-separated string,
so it can be driven per server via environment expansion:

```yaml
server:
  packs: ${MCP_BLUEPRINT_SERVER_PACKS:-}
```

With `MCP_BLUEPRINT_SERVER_PACKS=sakila` the server exposes only the Sakila
tools; `MCP_BLUEPRINT_SERVER_PACKS=pg-dba` only the DBA tools.  This lets two
MCP server entries share one configuration directory while serving different
pack sets against different databases.

## Tool definition

Each tool is a single YAML file:

```yaml
name: get_customer
description: Return a customer by identifier.

parameters:
  customer_id:
    type: integer
    required: true
    description: Unique customer identifier.

sql: ../sql/get_customer.sql

cache:
  ttl: 30

roles:
  - dba
  - readonly

enabled: true
requires_confirmation: false

format:
  rename:
    customer_name: name
  hidden:
    - internal_id
```

### Engine declaration

The engine of a pack is declared once in `pack.yaml`:

```yaml
# packs/my-pack/pack.yaml
name: my-pack
engines: [postgresql]
```

Tools in a single-engine pack use a plain `sql` path:

```yaml
name: get_users
description: List database users.
sql: ../sql/get_users.sql
```

### Multi-engine tools

A pack can share a tool across engines when its SQL differs per engine.  Two
per-tool forms override the pack default:

**`sql` as a map keyed by engine** — the tool exists for an engine only when it
has a SQL entry for it:

```yaml
name: get_users
description: List database users.

sql:
  postgresql: ../sql/postgresql/get_users.sql
  mysql:      ../sql/mysql/get_users.sql
```

**A shared `sql` path with an `engines` list** — for SQL that is identical
across engines (or engine-neutral):

```yaml
name: get_maintenance_status
description: Report maintenance-related metrics.

engines: [postgresql]
sql: ../sql/get_maintenance_status.sql
```

At load time the framework keeps only the packs and tools that can run on the
configured engine (`database.engine`).  Supported canonical engine identifiers
are `postgresql`, `mysql` and `oracle` (with `postgres` accepted as an alias).

### Fields

| Field                  | Type                 | Description                                        |
| ---------------------- | -------------------- | -------------------------------------------------- |
| `name`                 | string               | Tool name, lowercase with underscores.             |
| `description`          | string               | Short description shown to the LLM.                |
| `parameters`           | map of parameters    | Each parameter has `type`, `required`, `default`.  |
| `sql`                  | string or map        | SQL path, or map keyed by engine.                  |
| `engines`              | list of strings      | Optional; restricts a shared `sql` path to engines.|
| `cache.ttl`            | integer              | Cache TTL in seconds. Omit to use the default.     |
| `roles`                | list of strings      | Optional role metadata (reserved for authorization).|
| `enabled`              | boolean              | Set to `false` to hide the tool.                   |
| `requires_confirmation`| boolean              | Reserved for confirmation workflows.               |
| `writes`               | boolean              | Set to `true` to allow non-SELECT statements (opt-in). |
| `format.rename`        | map                  | Rename result columns.                             |
| `format.hidden`        | list of strings      | Drop internal columns from results.                |

If both `sql` (map) and `engines` are present, the `engines` list must match
the keys of the `sql` map.

### Parameter types

| `type`   | Python annotation | Notes                                |
| -------- | ----------------- | ------------------------------------ |
| `string` | `str`             |                                      |
| `integer`| `int`             |                                      |
| `number` | `float`           |                                      |
| `boolean`| `bool`            | Accepts `true/false`, `1/0`, `yes/no`|

Parameters are optional unless `required: true`.  Missing optional parameters
fall back to `default` (often `null`).

When a tool declares parameters, its SQL may use psycopg3 named placeholders
(`%(name)s`).  Literal `%` characters in the same statement must be doubled
(`%%`): the drivers parse `%` sequences as placeholders as soon as parameters
are bound.  The reference packs already do this, e.g.
`packs/pg-dba/sql/get_largest_objects.sql` uses `NOT LIKE 'pg\_%%'`.

### Parameters in practice

`get_largest_objects` shows the recommended pattern: an optional filter that
falls back to the unfiltered query:

```yaml
name: get_largest_objects
description: Return the largest tables and indexes by size, ordered descending.
parameters:
  object_name:
    type: string
    required: false
    default: null
    description: SQL LIKE pattern matched against the object name.
sql: ../sql/get_largest_objects.sql
```

```sql
SELECT ...
WHERE c.relkind IN ('r', 'i', 'm', 'p')
{% if object_name %}
  AND c.relname LIKE %(object_name)s
{% endif %}
ORDER BY size_bytes DESC
LIMIT 32;
```

The Jinja2 block is skipped when the parameter is omitted, so the placeholder
is only emitted when a value is provided.  Optional filters are usually
substring searches; to avoid asking the agent for wildcards, wrap the value in
the SQL, e.g. `ILIKE '%%' || %(title)s || '%%'` (see `packs/sakila`).

## SQL files

SQL lives in dedicated files and is rendered by Jinja2.

* Parameters use psycopg3 named placeholders: `%(name)s`.
* Conditional blocks are expressed with Jinja2:

```sql
SELECT *
FROM pg_stat_activity
{% if database %}
WHERE datname = %(database)s
{% endif %}
ORDER BY backend_start;
```

When the parameter is not provided the corresponding filter is omitted from
the final statement.

The `sql` path is resolved relative to the tool YAML file:

```
packs/my-pack/tools/get_customer.yaml
packs/my-pack/sql/get_customer.sql
```

is referenced with `sql: ../sql/get_customer.sql`.

### SQL layout

Single-engine packs store one SQL file per tool at the top level of `sql/`:

```
packs/my-pack/
    pack.yaml
    tools/
        get_users.yaml
    sql/
        get_users.sql
```

Multi-engine packs store one SQL file per engine:

```
packs/audit/
    pack.yaml
    tools/
        get_users.yaml
    sql/
        postgresql/
            get_users.sql
        mysql/
            get_users.sql
```

Engine identifiers in the `sql` map must match the directory names under
`sql/`.

## Security model

Every tool is **read-only by default**.  The framework enforces this twice:

* **At load time**, each SQL template is validated and a non-compliant pack is
  rejected with a clear error (tool, pack and file are reported).
* **At runtime**, the *rendered* statement is re-checked immediately before
  execution, so the policy cannot be bypassed through templates.

The guard is fail-closed: anything that is not a recognized read statement is
treated as a write and blocked.

### Read-only policy

The default policy allows exactly **one** `SELECT` statement (a `WITH` /
`WITH RECURSIVE` query is accepted when it ends in a `SELECT`).  Stacked or
trailing statements are rejected.

To let a tool modify data, opt in explicitly in the tool metadata:

```yaml
name: reset_password
description: Reset a password.
writes: true
sql: ../sql/reset_password.sql
```

A `writes: true` tool must still contain a single statement (no stacked
queries).  Opting in is the only way to run non-SELECT statements — editing
the SQL alone is not enough.

### Injection and templates

Templates support Jinja2 control flow (`{% if %}`, `{% endif %}`) but
**not** value interpolation (`{{ expr }}` is rejected).  Parameter values
reach the database exclusively as bound placeholders (`%(name)s`), so user
input can never become SQL syntax.

### Result size

The server caps the number of rows returned by a single tool call
(`server.max_rows`, default `1000`).  Tools that may return large result sets
should still use a `LIMIT`.

## KPI status convention

Diagnostic tools should return KPI rows so an agent can judge health at a
glance.  Each KPI row carries a `status` computed from the current value
against a suggested threshold:

| Column                | Description                               |
| --------------------- | ----------------------------------------- |
| `kpi_name`            | Stable machine-readable identifier.       |
| `current_value`       | Measured value.                           |
| `unit`                | e.g. `percent`, `bytes`, `count`.         |
| `suggested_threshold` | Value beyond which the KPI is unhealthy.  |
| `status`              | `ok`, `warning` or `error`.               |

Every KPI query returns one row per KPI (never filters rows out on severity),
so the agent always sees the full dashboard.

## Template pack

`template/pack` is a minimal skeleton for authoring new packs:

```
template/pack/
    pack.yaml
    tools/
        get_items.yaml
    sql/
        get_items.sql
```

It is **not** auto-loaded by the framework.  Create a new pack by copying the
template (or an existing pack such as `packs/pg-dba`) and replacing tool names,
descriptions and SQL queries.  See `template/README.md` for the workflow.

## Adding a new tool

1. Create `sql/<name>.sql` with the query.
2. Create `tools/<name>.yaml` with the metadata.

No Python code is required.  The framework loads the tool automatically on the
next server start.

## Guidelines

* Expose **concepts**, not SQL: `get_connections`, not `execute_sql`.
* Keep the number of tools small and meaningful.
* Never embed SQL in Python; it belongs in `sql/`.
* Prefer optional filters over separate near-identical tools.
