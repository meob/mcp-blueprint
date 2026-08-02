# Quick start

## 1. Configure the database

Edit `config/database.yaml` or export the connection string:

```bash
export MCP_BLUEPRINT_DATABASE_URL="postgresql://user:password@localhost:5432/mydb"
```

Every value in a YAML configuration file supports environment expansion:

```yaml
database:
  engine: postgresql
  dsn: ${MCP_BLUEPRINT_DATABASE_URL:-postgresql://meo@localhost:5432/pgbench}
```

## 2. List the available tools

```bash
uv run blueprint list-tools --config config
```

Output:

```
get_active_sessions
get_blocking_sessions
get_connections
get_database_size
get_long_running_queries
get_replication_status
get_wait_events
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

The exposed tools are domain-oriented.  Ask for information, not SQL:

* "how many connections are active on pgbench?"
* "which queries are running longer than one minute?"
* "how big is each database?"
* "are there blocking sessions?"

The LLM chooses the tool; the tool hides the SQL.
