SELECT query_id AS id,
       user AS user,
       address AS client_host,
       elapsed AS duration_seconds,
       memory_usage AS memory_bytes,
       substring(query, 1, 200) AS current_query
FROM system.processes
ORDER BY query_id
LIMIT 100
