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
description: Describe the domain this pack covers.
```

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

### Multi-engine tools

A tool is engine-aware when its SQL differs per engine.  Two forms:

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

At load time the framework keeps only the tools that can run on the configured
engine (`database.engine`).  Supported canonical engine identifiers are
`postgresql`, `mysql` and `oracle` (with `postgres` accepted as an alias).

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

### Per-engine SQL layout

Multi-engine packs store one SQL file per engine:

```
packs/dba/
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
        postgresql/
            get_items.sql
```

It is **not** auto-loaded by the framework.  Create a new pack by copying the
template (or an existing pack such as `packs/dba`) and replacing tool names,
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
