SELECT 'stale_statistics' AS component,
       owner || '.' || table_name AS name,
       'last analyzed: ' || TO_CHAR(last_analyzed, 'YYYY-MM-DD HH24:MI:SS') AS detail,
       NULL AS metric
FROM dba_tab_statistics
WHERE stale_stats = 'YES'
  AND owner NOT IN ('SYS', 'SYSTEM')
UNION ALL
SELECT 'invalid_objects',
       owner || '.' || object_name,
       object_type,
       NULL
FROM dba_objects
WHERE status <> 'VALID'
  AND owner NOT IN ('SYS', 'SYSTEM')
ORDER BY component, name
FETCH FIRST 20 ROWS ONLY
