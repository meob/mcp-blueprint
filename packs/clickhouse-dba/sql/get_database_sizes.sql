SELECT database AS name,
       sum(rows) AS rows,
       sum(bytes_on_disk) AS size_bytes
FROM system.parts
GROUP BY database
ORDER BY size_bytes DESC
LIMIT 100
