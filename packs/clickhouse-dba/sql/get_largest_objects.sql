SELECT database AS schema,
       table AS name,
       any(engine) AS kind,
       sum(rows) AS estimated_rows,
       sum(bytes_on_disk) AS size_bytes
FROM system.parts
{% if object_name %}
WHERE table LIKE %(object_name)s
{% endif %}
GROUP BY database, table
ORDER BY size_bytes DESC
LIMIT 32
