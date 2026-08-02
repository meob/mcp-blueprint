SELECT * FROM (
    SELECT 'buffer_pool_hit_ratio_pct' AS kpi_name,
           ROUND(100.0 * bp_req / NULLIF(bp_req + bp_read, 0), 1) AS current_value,
           '%' AS unit,
           '> 95' AS suggested_threshold,
           CASE WHEN 100.0 * bp_req / NULLIF(bp_req + bp_read, 0) < 95 THEN 'warning' ELSE 'ok' END AS status
    FROM (
        SELECT (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Innodb_buffer_pool_read_requests') AS bp_req,
               (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Innodb_buffer_pool_reads') AS bp_read
    ) t
    UNION ALL
    SELECT 'rollback_pct',
           ROUND(COALESCE(100.0 * rollbacks / NULLIF(commits + rollbacks, 0), 0), 1),
           '%',
           '< 1',
           CASE WHEN COALESCE(100.0 * rollbacks / NULLIF(commits + rollbacks, 0), 0) >= 1 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Com_commit') AS commits,
               (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Com_rollback') AS rollbacks
    ) t
    UNION ALL
    SELECT 'temp_disk_tables_pct',
           ROUND(100.0 * disk_tmp / NULLIF(disk_tmp + mem_tmp, 0), 1),
           '%',
           '< 10',
           CASE WHEN 100.0 * disk_tmp / NULLIF(disk_tmp + mem_tmp, 0) >= 10 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Created_tmp_disk_tables') AS disk_tmp,
               (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Created_tmp_tables') AS mem_tmp
    ) t
    UNION ALL
    SELECT 'table_open_cache_usage_pct',
           ROUND(100.0 * open_tables / NULLIF(table_open_cache, 0), 1),
           '%',
           '< 80',
           CASE WHEN 100.0 * open_tables / NULLIF(table_open_cache, 0) >= 80 THEN 'warning' ELSE 'ok' END
    FROM (
        SELECT (SELECT CAST(VARIABLE_VALUE AS UNSIGNED)
                  FROM performance_schema.global_status
                 WHERE VARIABLE_NAME = 'Open_tables') AS open_tables,
               @@table_open_cache AS table_open_cache
    ) t
) kpi
ORDER BY kpi_name;
