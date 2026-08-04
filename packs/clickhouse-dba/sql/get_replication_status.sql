SELECT * FROM (
    SELECT 'cluster' AS component,
           cluster AS name,
           concat('shard ', toString(shard_num), ' replica ', toString(replica_num)) AS state,
           NULL AS lag_seconds,
           NULL AS lag_bytes,
           concat(host_name, ':', toString(port)) AS detail
    FROM system.clusters
    UNION ALL
    SELECT 'replica',
           table,
           if(is_session_expired, 'session_expired', 'ok'),
           toInt64(queue_size),
           NULL,
           concat(database, '.', table)
    FROM system.replicas
) x
ORDER BY component, name
