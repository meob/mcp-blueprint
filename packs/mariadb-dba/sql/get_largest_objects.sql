SELECT table_schema AS `schema`,
       table_name AS name,
       table_type AS kind,
       table_rows AS estimated_rows,
       ROUND(COALESCE(data_length, 0) + COALESCE(index_length, 0)) AS size_bytes,
       FORMAT(COALESCE(data_length, 0) + COALESCE(index_length, 0), 0) AS size
FROM information_schema.tables
WHERE table_schema NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys')
{% if object_name %}
  AND table_name LIKE %(object_name)s
{% endif %}
ORDER BY size_bytes DESC
LIMIT 32;
