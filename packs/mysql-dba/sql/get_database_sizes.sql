SELECT table_schema AS `database`,
       ROUND(SUM(data_length + index_length)) AS size_bytes
FROM information_schema.tables
WHERE table_type = 'BASE TABLE'
GROUP BY table_schema
ORDER BY size_bytes DESC
LIMIT 100;
