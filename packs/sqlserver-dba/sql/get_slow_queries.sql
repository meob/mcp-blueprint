SELECT TOP 30
       SUBSTRING(st.text, (qs.statement_start_offset/2)+1,
                  ((CASE qs.statement_end_offset WHEN -1 THEN DATALENGTH(st.text) ELSE qs.statement_end_offset END - qs.statement_start_offset)/2)+1) AS query,
       COALESCE(OBJECT_NAME(pa.object_id, pa.database_id), 'ad-hoc') AS [schema],
       qs.execution_count AS calls,
       qs.total_elapsed_time / 1000 AS total_ms,
       qs.total_elapsed_time / qs.execution_count / 1000 AS mean_ms,
       qs.max_elapsed_time / 1000 AS max_ms
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
CROSS APPLY (
    SELECT MAX(CASE pa.attribute WHEN 'objectid' THEN CAST(pa.value AS int) END) AS object_id,
           MAX(CASE pa.attribute WHEN 'dbid' THEN CAST(pa.value AS int) END) AS database_id
    FROM sys.dm_exec_plan_attributes(qs.plan_handle) pa
) pa
WHERE qs.execution_count > 0
ORDER BY qs.total_elapsed_time DESC
