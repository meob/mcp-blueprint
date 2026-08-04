SELECT VARIABLE_NAME AS name,
       VARIABLE_VALUE AS value,
       NULL AS unit,
       'global' AS context,
       'server' AS category,
       NULL AS description
FROM information_schema.global_variables
WHERE VARIABLE_NAME IN (
    'max_connections',
    'innodb_buffer_pool_size',
    'innodb_buffer_pool_instances',
    'innodb_log_file_size',
    'innodb_flush_log_at_trx_commit',
    'innodb_flush_method',
    'innodb_io_capacity',
    'innodb_io_capacity_max',
    'sort_buffer_size',
    'join_buffer_size',
    'read_buffer_size',
    'tmp_table_size',
    'max_heap_table_size',
    'max_allowed_packet',
    'thread_cache_size',
    'table_open_cache',
    'long_query_time',
    'slow_query_log',
    'wait_timeout',
    'interactive_timeout',
    'log_bin',
    'binlog_format',
    'sync_binlog'
)
ORDER BY name
LIMIT 100;
