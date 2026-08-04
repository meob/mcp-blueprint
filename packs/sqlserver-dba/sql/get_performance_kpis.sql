SELECT * FROM (
    SELECT 'buffer_cache_hit_ratio_pct' AS kpi_name,
           CONVERT(decimal(6,1), (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Buffer cache hit ratio')) AS current_value,
           '%' AS unit,
           '> 90' AS suggested_threshold,
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Buffer cache hit ratio') < 90 THEN 'warning' ELSE 'ok' END AS status
    UNION ALL
    SELECT 'page_life_expectancy',
           (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page life expectancy'),
           's', '> 300',
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page life expectancy') < 300 THEN 'warning' ELSE 'ok' END
    UNION ALL
    SELECT 'page_reads_per_sec',
           (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page reads/sec'),
           'reads/s', '< 100',
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page reads/sec') >= 100 THEN 'warning' ELSE 'ok' END
    UNION ALL
    SELECT 'page_writes_per_sec',
           (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page writes/sec'),
           'writes/s', '< 100',
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Buffer Manager%' AND counter_name = 'Page writes/sec') >= 100 THEN 'warning' ELSE 'ok' END
    UNION ALL
    SELECT 'sql_compilations_per_sec',
           (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%SQL Statistics%' AND counter_name = 'SQL Compilations/sec'),
           'comp/s', '< 50',
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%SQL Statistics%' AND counter_name = 'SQL Compilations/sec') >= 50 THEN 'warning' ELSE 'ok' END
    UNION ALL
    SELECT 'number_of_deadlocks',
           (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Locks%' AND counter_name = 'Number of Deadlocks/sec'),
           'deadlocks', '= 0',
           CASE WHEN (SELECT MAX(cntr_value) FROM sys.dm_os_performance_counters WHERE object_name LIKE '%Locks%' AND counter_name = 'Number of Deadlocks/sec') > 0 THEN 'error' ELSE 'ok' END
) kpi
ORDER BY kpi_name
