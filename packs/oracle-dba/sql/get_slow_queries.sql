SELECT SUBSTR(sql_text, 1, 200) AS query,
       parsing_schema_name AS schema,
       executions AS calls,
       ROUND(elapsed_time / 1000) AS total_ms,
       ROUND(elapsed_time / 1000 / NULLIF(executions, 0), 1) AS mean_ms,
       NULL AS max_ms,
       ROUND(buffer_gets / NULLIF(executions, 0), 1) AS avg_buffer_gets
FROM v$sqlarea
WHERE parsing_schema_name NOT IN ('SYS', 'SYSTEM')
  AND executions > 0
ORDER BY elapsed_time DESC
FETCH FIRST 30 ROWS ONLY
