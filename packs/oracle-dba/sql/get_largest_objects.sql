SELECT owner AS schema,
       segment_name AS name,
       segment_type AS kind,
       NULL AS estimated_rows,
       SUM(bytes) AS size_bytes,
       ROUND(SUM(bytes) / 1048576) || ' MB' AS "size"
FROM dba_extents
{% if object_name %}
WHERE segment_name LIKE %(object_name)s
{% endif %}
GROUP BY owner, segment_name, segment_type
ORDER BY size_bytes DESC
FETCH FIRST 32 ROWS ONLY
