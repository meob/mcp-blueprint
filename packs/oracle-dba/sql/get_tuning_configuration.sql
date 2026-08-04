SELECT name,
       value AS value,
       NULL AS unit,
       'instance' AS context,
       CASE WHEN isdefault = 'FALSE' THEN 'modified' ELSE 'default' END AS category,
       description
FROM v$parameter
WHERE name IN ('sga_target', 'sga_max_size', 'memory_target', 'memory_max_target',
               'pga_aggregate_target', 'shared_pool_size', 'db_cache_size', 'log_buffer',
               'sessions', 'processes', 'open_cursors', 'db_files', 'undo_retention',
               'audit_trail', 'compatible', 'db_block_size', 'db_recovery_file_dest_size',
               'control_files')
ORDER BY name
FETCH FIRST 100 ROWS ONLY
