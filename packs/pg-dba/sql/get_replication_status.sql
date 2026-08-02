SELECT * FROM (
    SELECT 'instance' AS component,
           current_database() AS name,
           CASE WHEN pg_is_in_recovery() THEN 'standby' ELSE 'primary' END AS state,
           NULL::bigint AS lag_seconds,
           NULL::numeric AS lag_bytes,
           CASE WHEN pg_is_in_recovery() THEN 'in recovery' ELSE 'not in recovery' END AS detail
) AS a
UNION ALL
SELECT * FROM (
    SELECT 'standby' AS component,
           COALESCE(client_addr::text, 'local') AS name,
           sync_state AS state,
           round(extract(epoch FROM (now() - reply_time)))::bigint AS lag_seconds,
           pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes,
           application_name AS detail
    FROM pg_stat_replication
) AS b
UNION ALL
SELECT * FROM (
    SELECT 'slot' AS component,
           slot_name AS name,
           slot_type AS state,
           NULL::bigint AS lag_seconds,
           CASE WHEN active THEN pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) ELSE 0 END AS lag_bytes,
           CASE WHEN active THEN 'active' ELSE 'inactive' END AS detail
    FROM pg_replication_slots
) AS c
ORDER BY component, lag_bytes DESC
LIMIT 100;
