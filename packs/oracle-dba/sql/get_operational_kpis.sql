SELECT * FROM (
    SELECT 'connections_usage_pct' AS kpi_name,
           ROUND(100.0 * sessions_current / NULLIF(sessions_max, 0), 1) AS current_value,
           '%' AS unit,
           '< 70' AS suggested_threshold,
           CASE WHEN 100.0 * sessions_current / NULLIF(sessions_max, 0) >= 70 THEN 'warning' ELSE 'ok' END AS status
    FROM (SELECT sessions_current, sessions_max FROM v$license) stats
    UNION ALL
    SELECT 'active_sessions', COUNT(*), 'sessions', '< 5',
           CASE WHEN COUNT(*) >= 5 THEN 'warning' ELSE 'ok' END
    FROM gv$session WHERE type = 'USER' AND status = 'ACTIVE'
    UNION ALL
    SELECT 'idle_sessions', COUNT(*), 'sessions', '< 100',
           CASE WHEN COUNT(*) >= 100 THEN 'warning' ELSE 'ok' END
    FROM gv$session WHERE type = 'USER' AND status = 'INACTIVE'
    UNION ALL
    SELECT 'waiting_locks', COUNT(*), 'locks', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM gv$lock WHERE request > 0
    UNION ALL
    SELECT 'long_running_queries', COUNT(*), 'queries', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM gv$session WHERE type = 'USER' AND status = 'ACTIVE' AND last_call_et > 300
    UNION ALL
    SELECT 'longest_query_seconds', NVL(MAX(last_call_et), 0), 's', '< 1800',
           CASE WHEN NVL(MAX(last_call_et), 0) >= 1800 THEN 'warning' ELSE 'ok' END
    FROM gv$session WHERE type = 'USER' AND status = 'ACTIVE'
    UNION ALL
    SELECT 'oldest_transaction_seconds', ROUND(NVL(MAX((SYSDATE - TO_DATE(start_time, 'MM/DD/RR HH24:MI:SS')) * 86400), 0)), 's', '< 3600',
           CASE WHEN NVL(MAX((SYSDATE - TO_DATE(start_time, 'MM/DD/RR HH24:MI:SS')) * 86400), 0) >= 3600 THEN 'warning' ELSE 'ok' END
    FROM v$transaction
) kpi
ORDER BY kpi_name
