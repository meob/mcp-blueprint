SELECT * FROM (
    SELECT 'connections_usage_pct' AS kpi_name,
           ROUND(100.0 * connections / NULLIF(max_connections, 0), 1) AS current_value,
           '%' AS unit,
           '< 70' AS suggested_threshold,
           CASE WHEN 100.0 * connections / NULLIF(max_connections, 0) >= 70 THEN 'warning' ELSE 'ok' END AS status
    FROM (
        SELECT (SELECT COUNT(*) FROM information_schema.processlist) AS connections,
               GREATEST(@@max_connections, 1) AS max_connections
    ) stats
    UNION ALL
    SELECT 'active_sessions', active_sessions, 'sessions', '< 5',
           CASE WHEN active_sessions >= 5 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COUNT(*) AS active_sessions
        FROM information_schema.processlist
        WHERE COMMAND <> 'Sleep'
    ) t
    UNION ALL
    SELECT 'idle_sessions', idle_sessions, 'sessions', '< 100',
           CASE WHEN idle_sessions >= 100 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COUNT(*) AS idle_sessions
        FROM information_schema.processlist
        WHERE COMMAND = 'Sleep'
    ) t
    UNION ALL
    SELECT 'waiting_locks', waiting_locks, 'locks', '= 0',
           CASE WHEN waiting_locks > 0 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COUNT(*) AS waiting_locks FROM information_schema.innodb_lock_waits
    ) t
    UNION ALL
    SELECT 'long_running_queries', long_running, 'queries', '= 0',
           CASE WHEN long_running > 0 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COUNT(*) AS long_running
        FROM information_schema.processlist
        WHERE COMMAND <> 'Sleep' AND TIME > 300
    ) t
    UNION ALL
    SELECT 'longest_query_seconds', longest_query_seconds, 's', '< 1800',
           CASE WHEN longest_query_seconds >= 1800 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COALESCE(MAX(TIME), 0) AS longest_query_seconds
        FROM information_schema.processlist
        WHERE COMMAND <> 'Sleep'
    ) t
    UNION ALL
    SELECT 'oldest_transaction_seconds', ROUND(oldest_transaction_seconds), 's', '< 3600',
           CASE WHEN oldest_transaction_seconds >= 3600 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT COALESCE(MAX(TIMESTAMPDIFF(SECOND, trx_started, NOW())), 0) AS oldest_transaction_seconds
        FROM information_schema.innodb_trx
    ) t
) kpi
ORDER BY kpi_name;
