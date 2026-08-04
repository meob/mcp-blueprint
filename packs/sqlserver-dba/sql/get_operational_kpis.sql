SELECT * FROM (
    SELECT 'connections_usage_pct' AS kpi_name,
           CONVERT(decimal(5,1), 100.0 * (SELECT COUNT(*) FROM sys.dm_exec_connections) / NULLIF(CONVERT(int, (SELECT value_in_use FROM sys.configurations WHERE name = 'user connections')), 0)) AS current_value,
           '%' AS unit,
           '< 70' AS suggested_threshold,
           CASE WHEN 100.0 * (SELECT COUNT(*) FROM sys.dm_exec_connections) / NULLIF(CONVERT(int, (SELECT value_in_use FROM sys.configurations WHERE name = 'user connections')), 0) >= 70 THEN 'warning' ELSE 'ok' END AS status
    UNION ALL
    SELECT 'active_sessions', COUNT(*), 'sessions', '< 5',
           CASE WHEN COUNT(*) >= 5 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_exec_requests
    UNION ALL
    SELECT 'user_sessions', COUNT(*), 'sessions', '< 100',
           CASE WHEN COUNT(*) >= 100 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_exec_sessions
    WHERE is_user_process = 1
    UNION ALL
    SELECT 'waiting_locks', COUNT(*), 'locks', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_tran_locks
    WHERE request_status = 'WAIT'
    UNION ALL
    SELECT 'long_running_queries', COUNT(*), 'queries', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_exec_requests
    WHERE total_elapsed_time > 300000
    UNION ALL
    SELECT 'longest_query_seconds', MAX(total_elapsed_time) / 1000, 's', '< 1800',
           CASE WHEN MAX(total_elapsed_time) / 1000 >= 1800 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_exec_requests
    UNION ALL
    SELECT 'oldest_transaction_seconds', MAX(DATEDIFF(second, transaction_begin_time, GETDATE())), 's', '< 3600',
           CASE WHEN MAX(DATEDIFF(second, transaction_begin_time, GETDATE())) >= 3600 THEN 'warning' ELSE 'ok' END
    FROM sys.dm_tran_active_transactions
) kpi
ORDER BY kpi_name
