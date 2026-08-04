SELECT 'instance' AS component,
       i.instance_name AS name,
       'primary' AS state,
       NULL AS lag_seconds,
       NULL AS lag_bytes,
       i.host_name AS detail
FROM v$instance i
UNION ALL
SELECT 'dataguard' AS component,
       d.db_unique_name AS name,
       d.dest_role AS state,
       NULL AS lag_seconds,
       NULL AS lag_bytes,
       d.parent_dbun AS detail
FROM v$dataguard_config d
