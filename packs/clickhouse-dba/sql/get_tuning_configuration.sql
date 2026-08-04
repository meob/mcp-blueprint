SELECT name,
       value AS value,
       'bytes' AS unit,
       'session' AS context,
       if(changed = 1, 'modified', 'default') AS category,
       default AS default_value
FROM system.settings
WHERE name IN ('max_memory_usage', 'max_memory_usage_for_all_queries', 'max_memory_usage_for_user',
               'max_bytes_before_external_group_by', 'max_bytes_before_external_sort',
               'max_concurrent_queries', 'max_threads', 'max_partitions_per_insert_block',
               'max_table_size_to_drop', 'max_partition_size_to_drop', 'mark_cache_size',
               'read_buffer_size', 'merge_tree_max_rows_to_use_cache', 'tcp_keep_alive_timeout',
               'background_pool_size', 'background_schedule_pool_size')
ORDER BY name
LIMIT 100
