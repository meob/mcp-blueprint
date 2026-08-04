SELECT 'instance' AS component,
       CONVERT(varchar, SERVERPROPERTY('Servername')) AS name,
       'primary' AS state,
       NULL AS lag_seconds,
       NULL AS lag_bytes,
       'standalone instance' AS detail
UNION ALL
SELECT 'availability_group',
       ag.name,
       ars.role_desc,
       NULL,
       NULL,
       CONCAT(ar.replica_server_name, ' - ', ars.synchronization_health_desc)
FROM sys.availability_groups ag
JOIN sys.availability_replicas ar ON ag.group_id = ar.group_id
LEFT JOIN sys.dm_hadr_availability_replica_states ars ON ar.replica_id = ars.replica_id
