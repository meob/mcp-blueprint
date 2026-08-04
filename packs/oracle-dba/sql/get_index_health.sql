SELECT 'invalid' AS component,
       owner || '.' || table_name AS table_name,
       index_name AS name,
       status AS detail,
       NULL AS metric
FROM dba_indexes
WHERE status <> 'VALID'
  AND owner NOT IN ('SYS', 'SYSTEM')
ORDER BY owner, index_name
FETCH FIRST 20 ROWS ONLY
