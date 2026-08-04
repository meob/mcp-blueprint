SELECT tablespace_name AS name,
       SUM(bytes) AS size_bytes,
       ROUND(SUM(bytes) / 1048576) || ' MB' AS "size"
FROM dba_data_files
GROUP BY tablespace_name
ORDER BY size_bytes DESC
FETCH FIRST 100 ROWS ONLY
