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
  convert_size:
    - total_bytes
```

### Fields

| Field                  | Type                 | Description                                        |
| ---------------------- | -------------------- | -------------------------------------------------- |
| `name`                 | string               | Tool name, lowercase with underscores.             |
| `description`          | string               | Short description shown to the LLM.                |
| `parameters`           | map of parameters    | Each parameter has `type`, `required`, `default`.  |
| `sql`                  | string               | SQL path, relative to the tool YAML file.          |
| `cache.ttl`            | integer              | Cache TTL in seconds. Omit to use the default.     |
| `roles`                | list of strings      | Optional role metadata (reserved for authorization).|
| `enabled`              | boolean              | Set to `false` to hide the tool.                   |
| `requires_confirmation`| boolean              | Reserved for confirmation workflows.               |
| `format.rename`        | map                  | Rename result columns.                             |
| `format.hidden`        | list of strings      | Drop internal columns from results.                |
| `format.convert_size`  | list of strings      | Convert byte columns to human-readable sizes.      |

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
