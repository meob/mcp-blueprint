# MCP Servers

This project exposes several MCP Blueprint servers.  Each server name is
prefixed to its tool names (e.g. `pg-dba-docker_get_connections`), so the
server a tool runs against is always identifiable from the tool name.

| Server          | Transport | Engine     | Pack       | Target database                                    |
| --------------- | --------- | ---------- | ---------- | -------------------------------------------------- |
| `pg-dba`        | stdio     | PostgreSQL | pg-dba     | Local `pgbench` database on localhost:5432          |
| `pg-sakila`     | stdio     | PostgreSQL | sakila     | Local `sakila` database on localhost:5432           |
| `mysql-dba`     | stdio     | MySQL      | mysql-dba  | Local `mysakila` database on localhost:3306         |
| `mysql-dba-docker` | stdio | MySQL    | mysql-dba  | Containerized MySQL 8 `mysakila` on localhost:3308  |
| `pg-dba-docker` | remote    | PostgreSQL | pg-dba     | Containerized PostgreSQL 16 (docker compose stack)  |
| `oracle-dba`    | stdio     | Oracle     | oracle-dba | Containerized Oracle 23 (PDB `FREEPDB1`) on localhost:1521 |
| `clickhouse-dba`| stdio     | ClickHouse | clickhouse-dba | Containerized ClickHouse 24.8 on localhost:9000 |
| `sqlserver-dba` | stdio     | SQL Server | sqlserver-dba | Containerized SQL Server 2022 on localhost:1433 |
| `mariadb-dba`   | stdio     | MariaDB    | mariadb-dba | Containerized MariaDB 11.4 `mysakila` on localhost:3307 |

## Routing rules

* Always call the tool whose server prefix matches the target environment.
* "the Docker / containerized database" -> use `pg-dba-docker_*` tools.
* "the local PostgreSQL / localhost" -> use `pg-dba_*` tools.
* "the local MySQL / localhost" -> use `mysql-dba_*` tools.
* "the containerized MySQL / 3308" -> use `mysql-dba-docker_*` tools.
* Sakila store questions -> use `pg-sakila_*` tools.
* MySQL questions -> use `mysql-dba_*` tools.
* Oracle container questions -> use `oracle-dba_*` tools.
* ClickHouse container questions -> use `clickhouse-dba_*` tools.
* SQL Server container questions -> use `sqlserver-dba_*` tools.
* MariaDB container questions -> use `mariadb-dba_*` tools.
* When the target is ambiguous, ask which server to use instead of guessing.
