# Quick start

## 1. Configure the database

Edit `config/database.yaml` or export the connection string:

```bash
export MCP_BLUEPRINT_DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
```

Every value in a YAML configuration file supports environment expansion:

```yaml
database:
  engine: ${MCP_BLUEPRINT_DATABASE_ENGINE:-postgresql}
  dsn: ${MCP_BLUEPRINT_DATABASE_URL:-postgresql://pgbench@localhost:5432/pgbench}
```

The engine also selects the pack: with `engine: postgresql` the `pg-dba` and
`sakila` packs load; with `engine: mysql` the `mysql-dba` pack loads.  The two
DBA packs expose the same tool names.  The engine is env-overridable too:

```bash
MCP_BLUEPRINT_DATABASE_ENGINE=mysql \
MCP_BLUEPRINT_DATABASE_URL="mysql://monitor:password@localhost:3306/mydb" \
uv run blueprint list-tools --config config
```

## 2. List the available tools

```bash
uv run blueprint list-tools --config config
```

With the default PostgreSQL engine the server exposes the four Sakila store
tools plus the twelve DBA tools:

```
get_customer_rentals
get_film
search_customer
search_films
get_database_sizes
get_database_version
get_index_health
get_largest_objects
get_maintenance_status
get_operational_kpis
get_performance_kpis
get_replication_status
get_security_kpis
get_slow_queries
get_tuning_configuration
get_users
```

## 3. Run the server over stdio

```bash
uv run blueprint serve --config config --transport stdio
```

Register it in OpenCode by adding to your MCP configuration:

```json
{
  "mcpServers": {
    "pg-dba": {
      "command": "uv",
      "args": ["run", "blueprint", "serve", "--config", "config", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-blueprint"
    }
  }
}
```

For Claude Desktop, the equivalent entry is:

```json
{
  "mcpServers": {
    "pg-dba": {
      "command": "/absolute/path/to/mcp-blueprint/.venv/bin/blueprint",
      "args": ["serve", "--config", "config", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-blueprint"
    }
  }
}
```

### Both packs in parallel

One server process serves exactly one engine.  To give an agent both packs
(e.g. to operate on a PostgreSQL and a MySQL environment in parallel),
register two MCP servers pointing at the same config directory with different
environment overrides.  The following OpenCode configuration exposes the
`pg-dba` and `mysql-dba` servers side by side:

```json
{
  "mcp": {
    "pg-dba": {
      "type": "local",
      "command": ["/absolute/path/to/mcp-blueprint/.venv/bin/blueprint", "serve", "--config", "config", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-blueprint",
      "environment": {
        "MCP_BLUEPRINT_DATABASE_ENGINE": "postgresql",
        "MCP_BLUEPRINT_DATABASE_URL": "postgresql://pgbench@localhost:5432/pgbench"
      }
    },
    "mysql-dba": {
      "type": "local",
      "command": ["/absolute/path/to/mcp-blueprint/.venv/bin/blueprint", "serve", "--config", "config", "--transport", "stdio"],
      "cwd": "/absolute/path/to/mcp-blueprint",
      "environment": {
        "MCP_BLUEPRINT_DATABASE_ENGINE": "mysql",
        "MCP_BLUEPRINT_DATABASE_URL": "mysql://monitor:password@localhost:3306/mydb"
      }
    }
  }
}
```

Each server loads only the packs matching its engine: on PostgreSQL the
`pg-dba` and `sakila` packs, on MySQL the `mysql-dba` pack.  The two DBA packs
expose the same 12 tool names across engines.  Restart the MCP client after
changing its configuration.

## 4. Run the server over Streamable HTTP

```bash
uv run blueprint serve --config config --transport http --port 8000
```

The server listens on `http://127.0.0.1:8000/mcp`.

Register it in OpenCode:

```json
{
  "mcpServers": {
    "pg-dba": {
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

## What to ask the LLM

The exposed tools are domain-oriented.  Ask for information, not SQL.

The Sakila store tools:

* "what should I recommend to a family with a 12-year-old?" → `search_films`
* "tell me more about this film" → `get_film`
* "is my customer returning the DVDs on time?" → `get_customer_rentals`

The DBA tools:

* "how is the database doing overall?" → `get_operational_kpis`
* "any performance problems right now?" → `get_performance_kpis`
* "are there security concerns?" → `get_security_kpis`
* "which database is the largest?" → `get_database_sizes`
* "what are the slowest statements?" → `get_slow_queries`
* "are indexes healthy?" → `get_index_health`

KPI tools return rows with a `status` of `ok`/`warning`/`error`, so the LLM can
answer with a diagnosis instead of a raw table dump.

The LLM chooses the tool; the tool hides the SQL.
