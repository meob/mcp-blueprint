SELECT database AS schema,
       table AS table_name,
       name AS name,
       type AS kind,
       expr AS detail,
       NULL AS metric
FROM system.data_skipping_indices
ORDER BY database, table, name
LIMIT 20
