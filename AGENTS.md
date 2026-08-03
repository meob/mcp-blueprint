# MCP Servers

This project exposes several MCP Blueprint servers.  Each server name is
prefixed to its tool names (e.g. `pg-dba-docker_get_connections`), so the
server a tool runs against is always identifiable from the tool name.

| Server          | Transport | Engine     | Pack       | Target database                                    |
| --------------- | --------- | ---------- | ---------- | -------------------------------------------------- |
| `pg-dba`        | stdio     | PostgreSQL | pg-dba     | Local `pgbench` database on localhost:5432          |
| `pg-sakila`     | stdio     | PostgreSQL | sakila     | Local `sakila` database on localhost:5432           |
| `mysql-dba`     | stdio     | MySQL      | mysql-dba  | Local `mysakila` database on localhost:3306         |
| `pg-dba-docker` | remote    | PostgreSQL | pg-dba     | Containerized PostgreSQL 16 (docker compose stack)  |

## Routing rules

* Always call the tool whose server prefix matches the target environment.
* "the Docker / containerized database" -> use `pg-dba-docker_*` tools.
* "the local PostgreSQL / localhost" -> use `pg-dba_*` tools.
* Sakila store questions -> use `pg-sakila_*` tools.
* MySQL questions -> use `mysql-dba_*` tools.
* When the target is ambiguous, ask which server to use instead of guessing.
