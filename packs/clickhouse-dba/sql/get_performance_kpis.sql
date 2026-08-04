SELECT * FROM (
    SELECT 'mark_cache_hit_ratio_pct' AS kpi_name,
           round(100.0 * hit / nullIf(hit + miss, 0), 2) AS current_value,
           '%' AS unit,
           '> 90' AS suggested_threshold,
           if(100.0 * hit / nullIf(hit + miss, 0) < 90, 'warning', 'ok') AS status
    FROM (SELECT (SELECT value FROM system.asynchronous_metrics WHERE metric = 'MarkCacheHits') AS hit,
                 (SELECT value FROM system.asynchronous_metrics WHERE metric = 'MarkCacheMisses') AS miss) stats
    UNION ALL
    SELECT 'memory_usage_pct',
           round(100.0 * (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking') / nullIf(toInt64((SELECT value FROM system.settings WHERE name = 'max_memory_usage')), 0), 2),
           '%', '< 80',
           if(100.0 * (SELECT value FROM system.metrics WHERE metric = 'MemoryTracking') / nullIf(toInt64((SELECT value FROM system.settings WHERE name = 'max_memory_usage')), 0) >= 80, 'warning', 'ok')
    UNION ALL
    SELECT 'failed_queries_ratio_pct',
           round(100.0 * (SELECT value FROM system.events WHERE event = 'FailedQuery') / nullIf((SELECT value FROM system.events WHERE event = 'Query'), 0), 2),
           '%', '< 1',
           if(100.0 * (SELECT value FROM system.events WHERE event = 'FailedQuery') / nullIf((SELECT value FROM system.events WHERE event = 'Query'), 0) >= 1, 'warning', 'ok')
    UNION ALL
    SELECT 'unfinished_merges', toFloat64(count()), 'merges', '< 10',
           if(count() >= 10, 'warning', 'ok')
    FROM system.merges
    UNION ALL
    SELECT 'expired_replicas', toFloat64(count()), 'replicas', '= 0',
           if(count() > 0, 'error', 'ok')
    FROM system.replicas
    WHERE is_session_expired = 1
) kpi
ORDER BY kpi_name
