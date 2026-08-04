# Pack Template

The template and the pack are two distinct objects:

* **template** — this directory: the minimal, reusable skeleton of a pack.
* **pack** — the concrete implementation, e.g. [`packs/pg-dba`](../packs/pg-dba)
  or [`packs/mysql-dba`](../packs/mysql-dba).

The template is *not* loaded by the framework: `packs/` is the only directory
scanned at startup.  Keeping the two separate lets you evolve the skeleton
without affecting deployed packs.

## Creating a new pack

1. Copy this directory into `packs/` and rename it:

   ```sh
   cp -r template/pack packs/my-pack
   ```

2. Edit `pack.yaml` (name, version, engines, description).

3. Replace the example tool with your own tools:
   * one `tools/<tool>.yaml` per tool, following `get_items.yaml`;
   * one SQL file per tool under `sql/`, following `get_items.sql`.

   To build a domain pack (for example a Sakila "business" pack), start from
   a reference pack instead: copy `packs/pg-dba` (or `packs/mysql-dba`), keep
   the tool layout and touch only the tool names, descriptions and SQL queries.

## Tool metadata reference

```yaml
name: get_items            # ^[a-z][a-z0-9_]*$
description: Free text shown to the agent.
parameters:                # optional
  limit:
    type: integer          # string | integer | number | boolean
    required: false
    default: 50
sql: ../sql/get_items.sql
cache:
  ttl: 30                  # seconds; omit for the global default
```

* The pack engine is declared once in `pack.yaml` (`engines: [postgresql]`);
  packs that do not match the configured engine are skipped at load time.
* `sql` may be a single path (the common case) or a map keyed by engine for a
  pack that shares a tool across engines.  A tool is available for an engine
  only when a SQL entry exists for it.  `engines: [postgresql]` restricts a
  single shared SQL file to those engines.
* SQL files may use Jinja2 templating (`{% if %}`) and psycopg named
  placeholders (`%(name)s`).  Queries must be a single statement, use a
  sensible `ORDER BY` and a `LIMIT`.

See [`docs/pack_development.md`](../docs/pack_development.md) for the full
guide.

## Further reading

* [`docs/tutorial.md`](../docs/tutorial.md) — step-by-step build of your own
  MCP server, with a complete worked example in
  [`examples/customers`](../examples/customers).
* [`docs/best_practices.md`](../docs/best_practices.md) — authoring checklist
  (naming, descriptions, `instructions`, KPI convention).
* [`docs/faq.md`](../docs/faq.md) — quick answers to common questions.
