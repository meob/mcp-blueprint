WITH stats AS (
    SELECT (SELECT count(*) FROM pg_stat_activity)                                   AS connections,
           GREATEST(current_setting('max_connections')::int, 1)                     AS max_connections,
           (SELECT count(*) FROM pg_stat_activity WHERE state = 'active')           AS active_sessions,
           (SELECT count(*) FROM pg_stat_activity
             WHERE state = 'idle in transaction'
               AND state_change < now() - interval '30 seconds')                    AS idle_in_transaction,
           (SELECT count(*) FROM pg_locks WHERE NOT granted)                        AS waiting_locks,
           (SELECT count(*) FROM pg_stat_activity
             WHERE state = 'active' AND query_start < now() - interval '5 minutes') AS long_running,
           (SELECT COALESCE(max(extract(epoch FROM (now() - query_start))), 0)
              FROM pg_stat_activity WHERE state = 'active')                         AS longest_query_seconds,
           (SELECT COALESCE(max(extract(epoch FROM (now() - xact_start))), 0)
              FROM pg_stat_activity WHERE xact_start IS NOT NULL)                   AS oldest_transaction_seconds,
           (SELECT count(*) FROM pg_stat_activity
             WHERE state <> 'idle'
               AND (query ILIKE 'vacuum%' OR query ILIKE 'analyze%'))               AS active_maintenance,
           (SELECT COALESCE(max(extract(epoch FROM (now() - reply_time))), 0)
              FROM pg_stat_replication)                                             AS replication_lag_seconds
)
SELECT * FROM (
    SELECT 'connections_usage_pct' AS kpi_name,
           round(100.0 * connections / max_connections, 1)::text AS current_value,
           '%' AS unit,
           '< 70' AS suggested_threshold,
           CASE WHEN 100.0 * connections / max_connections >= 70 THEN 'warning' ELSE 'ok' END AS status
    FROM stats
    UNION ALL
    SELECT 'active_sessions', active_sessions::text, 'sessions', '< 5',
           CASE WHEN active_sessions >= 5 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'idle_in_transaction_sessions', idle_in_transaction::text, 'sessions', '= 0',
           CASE WHEN idle_in_transaction > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'waiting_locks', waiting_locks::text, 'locks', '= 0',
           CASE WHEN waiting_locks > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'long_running_queries', long_running::text, 'queries', '= 0',
           CASE WHEN long_running > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'longest_query_seconds', round(longest_query_seconds)::text, 's', '< 1800',
           CASE WHEN longest_query_seconds >= 1800 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'oldest_transaction_seconds', round(oldest_transaction_seconds)::text, 's', '< 3600',
           CASE WHEN oldest_transaction_seconds >= 3600 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'active_maintenance_sessions', active_maintenance::text, 'sessions', '= 0',
           CASE WHEN active_maintenance > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'replication_lag_seconds', round(replication_lag_seconds)::text, 's', '< 1',
           CASE WHEN replication_lag_seconds >= 1 THEN 'warning' ELSE 'ok' END
    FROM stats
) kpi
ORDER BY kpi_name;
