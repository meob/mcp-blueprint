#!/usr/bin/env bash
set -euo pipefail

# One-shot bootstrap for the demo PostgreSQL instance (docker compose).
# Runs only on the first initialization of an empty data directory, as the
# POSTGRES_USER superuser (trust auth, no password needed).
#
# Creates the three roles the demo relies on:
#   dba        - superuser, for administration
#   app_owner  - owns the pgbench schema/tables (application owner)
#   monitor    - pg_monitor membership, used by the MCP server (least privilege)
# Enables pg_stat_statements, initializes the pgbench database at scale 1 and
# runs a short benchmark so the monitoring views have meaningful data.

DB_NAME="${POSTGRES_DB:-pgbench}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DB_NAME" <<-EOSQL
    CREATE ROLE dba LOGIN SUPERUSER PASSWORD 'dba';
    CREATE ROLE app_owner LOGIN PASSWORD 'app_owner';
    CREATE ROLE monitor LOGIN PASSWORD 'monitor' IN ROLE pg_monitor;

    CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

    ALTER DATABASE "$DB_NAME" OWNER TO app_owner;
EOSQL

# Create the pgbench schema owned by the application owner (scale 1).
# The default run also ANALYZEs at the end, giving the planner fresh stats.
pgbench --username app_owner --initialize --scale=1 "$DB_NAME"

# Short benchmark to populate pg_stat_statements and the pg_stat_* counters.
pgbench --username app_owner --client 4 --jobs 2 --time 10 "$DB_NAME"
