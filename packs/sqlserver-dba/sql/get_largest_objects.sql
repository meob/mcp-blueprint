SELECT TOP 32
       OBJECT_SCHEMA_NAME(t.object_id) AS [schema],
       t.name AS name,
       'table' AS kind,
       MAX(p.rows) AS estimated_rows,
       SUM(a.total_pages) * 8192 AS size_bytes,
       CONVERT(decimal(18,1), SUM(a.total_pages) * 8.0 / 1024) AS size_mb
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
{% if object_name %}
WHERE t.name LIKE %(object_name)s
{% endif %}
GROUP BY t.object_id, t.name
ORDER BY size_bytes DESC
