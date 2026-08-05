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
`sakila` packs load; with `engine: mysql` only `mysql-dba` loads; with
`oracle`, `clickhouse`, `sqlserver` or `mariadb` the matching `*-dba` pack
loads.  All six DBA packs expose the same 13 tool names.  The engine aliases
`postgres`, `mssql` and `sql_server` are accepted too.  The engine is
env-overridable:

```bash
MCP_BLUEPRINT_DATABASE_ENGINE=mysql \
MCP_BLUEPRINT_DATABASE_URL="mysql://monitor:password@localhost:3306/mydb" \
uv run blueprint list-tools --config config
```

The four extra engines are optional.  Install their drivers through the extras
and bring a database up with the provided compose stack (which also starts a
containerized MySQL 8 on `3308` for the `mysql-dba` pack):

```bash
uv sync --extra oracle --extra clickhouse --extra sqlserver   # or --all-extras
docker compose -f docker-compose.databases.yaml up -d
```

| Engine       | Example DSN                                                          |
| ------------ | -------------------------------------------------------------------- |
| `mysql`      | `mysql://monitor:monitor_pw@localhost:3308/mysakila`                 |
| `oracle`     | `oracle://monitor:monitor_pw@localhost:1521/FREEPDB1`                |
| `clickhouse` | `clickhouse://monitor:monitor_pw@localhost:9000/default`             |
| `sqlserver`  | `sqlserver://sa:YourStrong!Passw0rd@localhost:1433/master`           |
| `mariadb`    | `mariadb://monitor:monitor_pw@localhost:3307/mysakila`               |

See [docs/docker.md](docker.md) for the container defaults and the
least-privilege monitoring accounts the stack configures.

## 2. List the available tools

```bash
uv run blueprint list-tools --config config
```

With the default PostgreSQL engine the server exposes all engine-compatible
packs: the five Sakila store tools plus the thirteen DBA tools:

```
customer_account_summary
film_stock
recommend_films
rental_history
search_customer
get_connections
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

To expose a subset per server, restrict the pack allowlist via
`MCP_BLUEPRINT_SERVER_PACKS` (comma-separated pack names).  For example
`MCP_BLUEPRINT_SERVER_PACKS=sakila` loads only the five Sakila tools and
`MCP_BLUEPRINT_SERVER_PACKS=pg-dba` only the thirteen DBA tools.  See
`docs/pack_development.md` for details.

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
`pg-dba` and `sakila` packs, on MySQL the `mysql-dba` pack, and so on for any
of the six supported engines.  The DBA packs expose the same 13 tool names
across engines, so a prompt written against one engine also works against the
others.  Restart the MCP client after changing its configuration.

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

## 5. Run with Docker

The repository ships a `Dockerfile` and a `docker-compose.yaml` that start a
PostgreSQL instance and the `pg-dba` server over Streamable HTTP:

```bash
docker compose up --build
```

The server is then available at `http://localhost:8000/mcp`.  See
[docs/docker.md](docker.md) for configuration, health checks and production
notes.

## What to ask the LLM

The exposed tools are domain-oriented.  Ask for information, not SQL.

The Sakila store tools:

* "what should I recommend to a family with a 12-year-old?" → `recommend_films`
* "is my customer returning the DVDs on time?" → `customer_account_summary`
* "what films has this customer rented before?" → `rental_history`
* "is Academy Dinosaur in stock at store 2?" → `film_stock`

The DBA tools:

* "how is the database doing overall?" → `get_operational_kpis`
* "any performance problems right now?" → `get_performance_kpis`
* "are there security concerns?" → `get_security_kpis`
* "who is connected to the database?" → `get_connections`
* "which database is the largest?" → `get_database_sizes`
* "what are the slowest statements?" → `get_slow_queries`
* "are indexes healthy?" → `get_index_health`

KPI tools return rows with a `status` of `ok`/`warning`/`error`, so the LLM can
answer with a diagnosis instead of a raw table dump.

The LLM chooses the tool; the tool hides the SQL.

## Next steps

To build your own server for your own application or database, follow
[docs/tutorial.md](tutorial.md).  The authoring checklist lives in
[docs/best_practices.md](best_practices.md) and quick answers in
[docs/faq.md](faq.md).
