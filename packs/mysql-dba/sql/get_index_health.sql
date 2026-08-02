SELECT 'unused' AS component,
       CONCAT(OBJECT_SCHEMA, '.', OBJECT_NAME) AS table_name,
       INDEX_NAME AS name,
       CONCAT(FORMAT(SUM_TIMER_WAIT / 1000000, 0), ' ms') AS detail,
       COUNT_STAR AS metric
FROM performance_schema.table_io_waits_summary_by_index_usage
WHERE INDEX_NAME IS NOT NULL
  AND INDEX_NAME <> 'PRIMARY'
  AND COUNT_STAR = 0
ORDER BY COUNT_STAR DESC
LIMIT 20;
