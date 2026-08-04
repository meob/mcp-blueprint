# Build your own MCP server

mcp-blueprint turns a database into a set of domain-oriented MCP tools.  You
do **not** write Python: a server is described entirely by *packs* — YAML
tool metadata plus SQL files.  This guide walks you through building your own
server for your application or database, from cloning to registering the MCP
client.

## Choose how you consume the framework

Two usage models exist; they only differ in where your packs live and how you
upgrade.

**Model A — clone the repository** (fastest to start).  Your packs live
inside the cloned repo under `packs/`.  Upgrading means pulling the
repository, which mixes your work with the framework's history.

**Model B — mcp-blueprint as a dependency** (recommended for real projects).
Your packs live in your own repository.  You install mcp-blueprint as a
package and point `server.packs_dir` at your packs.  Upgrading the framework
is a dependency bump that never touches your packs.

This guide follows Model A first because it is the quickest, and shows the
changes needed for Model B in [Updating without breaking your packs](#7-updating-without-breaking-your-packs).

## 1. Get the code

```sh
git clone https://github.com/meob/mcp-blueprint.git
cd mcp-blueprint
uv sync --all-extras --dev
uv run blueprint --help
```

## 2. Plan the pack

Before writing files, decide the *concepts* your agent will need.  A tool is
a question the agent should be able to answer, not a SQL statement.  See
[docs/best_practices.md](best_practices.md) for the full checklist; the short
version:

* 4–8 tools per domain pack.
* Verb-first `snake_case` names: `get_`, `search_`, `list_`.
* Precise, concise descriptions **in English**, telling the agent what it
  learns and the edge cases (for example "returns no rows when not found").
* A short `instructions` block that guides tool order and domain logic.

This guide builds a small CRM pack with these tools:

| Tool                  | Question it answers                    |
| --------------------- | -------------------------------------- |
| `search_customers`    | Who are the customers matching a name/city? |
| `get_customer`        | What is this customer's record and order summary? |
| `get_customer_orders` | Which orders does this customer have?  |
| `get_orders_kpis`     | Is overall order health good?          |

## 3. Create the pack

Copy the template:

```sh
cp -r template/pack packs/my-app
```

Edit `packs/my-app/pack.yaml`:

```yaml
name: my-app
version: 1.0.0
engines: [postgresql]
description: >-
  Customer management pack for a small CRM database.
instructions: >-
  When a customer asks about their account, first call search_customers to
  find the customer identifier, then get_customer and get_customer_orders
  for the details.
```

Each tool is one YAML file plus one SQL file:

```yaml
# packs/my-app/tools/get_customer.yaml
name: get_customer
description: >-
  Return the full record for a single customer.  Returns one row, or none
  when the customer does not exist.
parameters:
  customer_id:
    type: integer
    required: true
    description: Unique customer identifier.
sql: ../sql/get_customer.sql
```

```sql
-- packs/my-app/sql/get_customer.sql
SELECT c.customer_id, c.full_name, c.email, c.city
FROM customers c
WHERE c.customer_id = %(customer_id)s;
```

A fully worked example (schema, seed data, KPI dashboard) ships in
[`examples/customers`](../examples/customers).  Copy it instead of the
template if you want to start from a complete CRM pack.

## 4. Configure the server

The engine and connection string live in `config/database.yaml`; the server
name and pack directory in `config/server.yaml`:

```yaml
# config/database.yaml
database:
  engine: postgresql
  dsn: postgresql://user:password@localhost:5432/mydb
```

```yaml
# config/server.yaml
server:
  name: my-app-server
  packs_dir: packs
```

`database.engine` also selects which packs load: the example above declares
`engines: [postgresql]`, so it loads on a PostgreSQL engine and is skipped
on any other.

## 5. Validate and run

```sh
uv run blueprint list-tools --config config    # shows exactly your tools
uv run blueprint serve --config config --transport stdio
```

Start on the HTTP transport with:

```sh
uv run blueprint serve --config config --transport http --port 8000
# endpoint: http://127.0.0.1:8000/mcp
```

The framework validates every SQL template at startup and refuses to load a
non-compliant pack, so `list-tools` is also your safety check after editing.

## 6. Register the client

OpenCode (see `examples/opencode.json`):

```json
{
  "mcpServers": {
    "my-app": {
      "command": "uv",
      "args": ["run", "blueprint", "serve", "--config", "config", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-blueprint"
    }
  }
}
```

Claude Desktop (`examples/claude_desktop.json`) uses the `.venv/bin/blueprint`
executable instead.  Restart the MCP client after changing its configuration.

## 7. Updating without breaking your packs

**Model B (dependency).**  Keep your packs in your own repository, declare
mcp-blueprint as a dependency and point `packs_dir` at your pack directory:

```yaml
server:
  packs_dir: /path/to/your/packs
```

Upgrading is a dependency bump (`uv add mcp-blueprint@latest && uv lock`).
The pack contract (`pack.yaml`, `tools/*.yaml`, `sql/*`) is stable and
additive, so your packs keep working.  If anything ever becomes incompatible,
the load-time validation fails loudly at `list-tools` time — never silently.

**Model A (fork).**  Do not keep your packs next to the reference packs
permanently; move them to your own repository and use the allowlist
(`MCP_BLUEPRINT_SERVER_PACKS=my-app`) to load only what you need.  Track new
framework features through `template/` and `docs/best_practices.md` rather
than by editing reference packs.

New engines arrive as opt-in: add them to `engines:` in `pack.yaml` only when
you actually support that database.

## Next steps

* [docs/best_practices.md](best_practices.md) — the full authoring checklist.
* [docs/faq.md](faq.md) — quick answers to common questions.
* [docs/pack_development.md](pack_development.md) — pack format reference.
* [docs/quickstart.md](quickstart.md) — running the packs shipped with the
  framework.
