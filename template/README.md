# Pack Template

The template and the pack are two distinct objects:

* **template** — this directory: the minimal, reusable skeleton of a pack.
* **pack** — the concrete implementation, e.g. [`packs/dba`](../packs/dba).

The template is *not* loaded by the framework: `packs/` is the only directory
scanned at startup.  Keeping the two separate lets you evolve the skeleton
without affecting deployed packs.

## Creating a new pack

1. Copy this directory into `packs/` and rename it:

   ```sh
   cp -r template/pack packs/my-pack
   ```

2. Edit `pack.yaml` (name, version, description).

3. Replace the example tool with your own tools:
   * one `tools/<tool>.yaml` per tool, following `get_items.yaml`;
   * one SQL file per tool under `sql/<engine>/`, following `get_items.sql`.

   To build a domain pack (for example a Sakila "business" pack), start from
   the DBA pack instead: copy `packs/dba`, keep the tool layout and touch only
   the tool names, descriptions and SQL queries.

## Tool metadata reference

```yaml
name: get_items            # ^[a-z][a-z0-9_]*$
description: Free text shown to the agent.
parameters:                # optional
  limit:
    type: integer          # string | integer | number | boolean
    required: false
    default: 50
sql:
  postgresql: ../sql/postgresql/get_items.sql
  # mysql:     ../sql/mysql/get_items.sql        # add an engine to support it
cache:
  ttl: 30                  # seconds; omit for the global default
```

* `sql` may be a single path (same file for every engine) or a map keyed by
  engine.  A tool is available for an engine only when a SQL entry exists for
  it.  Tools that cannot run on the configured engine are skipped at load time.
* `engines: [postgresql]` restricts a single shared SQL file to those engines.
* SQL files may use Jinja2 templating (`{% if %}`) and psycopg named
  placeholders (`%(name)s`).  Queries must be a single statement, use a
  sensible `ORDER BY` and a `LIMIT`.

See [`docs/pack_development.md`](../docs/pack_development.md) for the full
guide.
