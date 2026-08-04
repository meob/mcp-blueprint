SELECT * FROM (
    SELECT 'connections_usage_pct' AS kpi_name,
           round(100.0 * sum(if(metric IN ('TCPConnection', 'HTTPConnection', 'InterserverConnection'), value, 0)) / nullIf(toInt32((SELECT value FROM system.settings WHERE name = 'max_concurrent_queries')), 0), 1) AS current_value,
           '%' AS unit,
           '< 70' AS suggested_threshold,
           if(100.0 * sum(if(metric IN ('TCPConnection', 'HTTPConnection', 'InterserverConnection'), value, 0)) / nullIf(toInt32((SELECT value FROM system.settings WHERE name = 'max_concurrent_queries')), 0) >= 70, 'warning', 'ok') AS status
    FROM system.metrics
    WHERE metric IN ('TCPConnection', 'HTTPConnection', 'InterserverConnection')
    UNION ALL
    SELECT 'active_sessions', toFloat64(count()), 'sessions', '< 5',
           if(count() >= 5, 'warning', 'ok')
    FROM system.processes
    UNION ALL
    SELECT 'running_queries', toFloat64((SELECT value FROM system.metrics WHERE metric = 'Query')), 'queries', '< 5',
           if((SELECT value FROM system.metrics WHERE metric = 'Query') >= 5, 'warning', 'ok')
    UNION ALL
    SELECT 'tcp_connections', toFloat64((SELECT value FROM system.metrics WHERE metric = 'TCPConnection')), 'connections', '< 100',
           if((SELECT value FROM system.metrics WHERE metric = 'TCPConnection') >= 100, 'warning', 'ok')
    UNION ALL
    SELECT 'long_running_queries', toFloat64(count()), 'queries', '= 0',
           if(count() > 0, 'warning', 'ok')
    FROM system.processes
    WHERE elapsed > 300
    UNION ALL
    SELECT 'longest_query_seconds', toFloat64(max(elapsed)), 's', '< 1800',
           if(max(elapsed) >= 1800, 'warning', 'ok')
    FROM system.processes
    UNION ALL
    SELECT 'pending_mutations', toFloat64(count()), 'mutations', '= 0',
           if(count() > 0, 'warning', 'ok')
    FROM system.mutations
    WHERE is_done = 0
) kpi
ORDER BY kpi_name
