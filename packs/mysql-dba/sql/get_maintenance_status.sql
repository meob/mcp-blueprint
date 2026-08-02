SELECT 'fragmented_tables' AS component,
       table_schema AS name,
       CONCAT(FORMAT(data_free, 0), ' bytes free') AS detail,
       data_free AS metric
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
  AND data_free > 10485760
  AND data_free > (data_length + index_length) * 0.10
ORDER BY data_free DESC
LIMIT 10;
