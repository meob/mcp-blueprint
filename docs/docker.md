# Docker

Run MCP Blueprint as a containerized Streamable HTTP server.  The image ships
the framework, the reference configuration and the packs; the database is a
separate service.

## Quick start with Docker Compose

The repository provides a `docker-compose.yaml` that starts a PostgreSQL 16
instance and a `blueprint` server exposing the `pg-dba` pack over Streamable
HTTP:

```bash
docker compose up --build
```

Wait for both containers to become healthy, then point an MCP client at
`http://localhost:8000/mcp`.  For example, in OpenCode:

```json
{
  "mcpServers": {
    "pg-dba": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

The server listens on port `8000` (the Streamable HTTP endpoint is `/mcp`).
Stop the stack with `docker compose down`; add `-v` to also remove the
PostgreSQL volume.

## Building the image manually

```bash
docker build -t mcp-blueprint .
```

The default command runs the server over Streamable HTTP:

```bash
docker run --rm -p 8000:8000 \
  -e MCP_BLUEPRINT_DATABASE_URL="postgresql://user:password@host:5432/db" \
  mcp-blueprint
```

## Configuration

All values are overridable through environment variables thanks to the
`${VAR:-default}` expansion in the YAML files under `config/`.  The most
relevant ones:

| Variable                           | Purpose                                        |
| ---------------------------------- | ---------------------------------------------- |
| `MCP_BLUEPRINT_DATABASE_ENGINE`    | Engine selecting the adapter and packs (`postgresql`, `mysql`, ...). |
| `MCP_BLUEPRINT_DATABASE_URL`       | Connection string for the configured engine.   |
| `MCP_BLUEPRINT_SERVER_PACKS`       | Comma-separated pack allowlist (e.g. `pg-dba`). |

To use a different configuration directory, override the command, for example
with a config mounted from the host:

```bash
docker run --rm -p 8000:8000 \
  -v "$PWD/my-config:/app/config" \
  mcp-blueprint
```

To run over stdio instead (for a desktop client), override the command:

```bash
docker run --rm -i mcp-blueprint \
  blueprint serve --config config --transport stdio
```

## Health check

The compose stack uses a TCP connect on port `8000` as the container
healthcheck for the `blueprint` service and `pg_isready` for PostgreSQL.
`docker compose ps` shows the resulting state.

## Metrics

Prometheus metrics are disabled by default (`config/metrics.yaml`).  To enable
them, mount a metrics configuration with `enabled: true` or extend the command;
the endpoint is served on a separate `host:port/metrics` address that works
alongside the MCP transport.

## Notes

* The container runs as an unprivileged user and only needs a writable `logs/`
  directory for the rotating log and audit files.
* The `postgres` service in `docker-compose.yaml` uses
  `POSTGRES_HOST_AUTH_METHOD: trust` for password-less local development; do
  not reuse this configuration for a real deployment.
* Builds use the `uv` builder image and `python:3.12-slim` at runtime; the
  image does not require a compiler toolchain.
