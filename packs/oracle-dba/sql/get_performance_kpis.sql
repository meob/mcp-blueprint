SELECT * FROM (
    SELECT 'buffer_cache_hit_ratio_pct' AS kpi_name,
           ROUND(100 * (1 - phys / NULLIF(logical, 0)), 1) AS current_value,
           '%' AS unit,
           '> 90' AS suggested_threshold,
           CASE WHEN 100 * (1 - phys / NULLIF(logical, 0)) < 90 THEN 'warning' ELSE 'ok' END AS status
    FROM (SELECT SUM(CASE WHEN name = 'physical reads' THEN value ELSE 0 END) AS phys,
                 SUM(CASE WHEN name IN ('db block gets', 'consistent gets') THEN value ELSE 0 END) AS logical
          FROM v$sysstat
          WHERE name IN ('physical reads', 'db block gets', 'consistent gets')) stats
    UNION ALL
    SELECT 'library_cache_miss_pct',
           ROUND(100.0 * SUM(reloads) / NULLIF(SUM(pins), 0), 2), '%', '< 1',
           CASE WHEN 100.0 * SUM(reloads) / NULLIF(SUM(pins), 0) >= 1 THEN 'warning' ELSE 'ok' END
    FROM v$librarycache
    UNION ALL
    SELECT 'dictionary_cache_miss_pct',
           ROUND(100.0 * SUM(getmisses) / NULLIF(SUM(gets), 0), 2), '%', '< 10',
           CASE WHEN 100.0 * SUM(getmisses) / NULLIF(SUM(gets), 0) >= 10 THEN 'warning' ELSE 'ok' END
    FROM v$rowcache
    UNION ALL
    SELECT 'redo_log_space_requests',
           SUM(CASE WHEN name = 'redo log space requests' THEN value ELSE 0 END), 'requests', '= 0',
           CASE WHEN SUM(CASE WHEN name = 'redo log space requests' THEN value ELSE 0 END) > 0 THEN 'warning' ELSE 'ok' END
    FROM v$sysstat
    WHERE name = 'redo log space requests'
    UNION ALL
    SELECT 'sorts_disk_pct',
           ROUND(100.0 * disk / NULLIF(disk + mem, 0), 2), '%', '< 5',
           CASE WHEN 100.0 * disk / NULLIF(disk + mem, 0) >= 5 THEN 'warning' ELSE 'ok' END
    FROM (SELECT SUM(CASE WHEN name = 'sorts (disk)' THEN value ELSE 0 END) AS disk,
                 SUM(CASE WHEN name = 'sorts (memory)' THEN value ELSE 0 END) AS mem
          FROM v$sysstat
          WHERE name IN ('sorts (disk)', 'sorts (memory)')) stats
) kpi
ORDER BY kpi_name
