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

## Extra database engines

The `docker-compose.databases.yaml` file brings up the containerized MySQL
(used by the `mysql-dba` pack) plus one container for each of the four optional
engines, used by the `oracle-dba`, `clickhouse-dba`, `sqlserver-dba` and
`mariadb-dba` packs:

```bash
docker compose -f docker-compose.databases.yaml up -d
```

| Service     | Image                        | Host port     | Monitoring login            |
| ----------- | ---------------------------- | ------------- | --------------------------- |
| `mysql`     | `mysql:8`                    | `3308`        | `monitor` / `monitor_pw`    |
| `oracle`    | `gvenzl/oracle-free:23-slim` | `1521`        | `monitor` / `monitor_pw` (PDB `FREEPDB1`) |
| `clickhouse`| `clickhouse/clickhouse-server:24.8` | `9000` (native), `8123` (HTTP) | `monitor` / `monitor_pw` |
| `sqlserver` | `mcr.microsoft.com/mssql/server:2022-latest` | `1433` | `sa` / `YourStrong!Passw0rd` |
| `mariadb`   | `mariadb:11.4`               | `3307`        | `monitor` / `monitor_pw`    |

First startup of the Oracle container initializes a database and can take
several minutes.  The least-privilege grants for the monitoring users are
applied once on first boot by the scripts under `docker/init/` (MySQL and
MariaDB `PROCESS`/`REPLICATION CLIENT`/`SELECT`, Oracle
`SELECT ANY DICTIONARY`); SQL Server is reached as `sa`, which already holds
the required permissions.  The MySQL and MariaDB containers also load the
official [Sakila sample database](https://dev.mysql.com/doc/sakila/en/) into
their `mysakila` database on first boot (`docker/init/sakila/`), so the DBA
tools return meaningful data; the Oracle init script switches to the
`FREEPDB1` pluggable database before granting, since the `monitor` user lives
there.

The integration tests under `tests/test_pack_engine_integration.py` connect to
these defaults and skip when the engine is unreachable.  Host port `3306` is
left unused by the compose stack because it is reserved for the local
`mysakila` instance used by `mysql-dba`; the containerized MySQL listens on
`3308` instead.

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
