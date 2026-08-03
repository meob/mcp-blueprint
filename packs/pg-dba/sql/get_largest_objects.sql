SELECT n.nspname                                  AS schema,
       c.relname                                  AS name,
       CASE c.relkind
           WHEN 'r' THEN 'table'
           WHEN 'i' THEN 'index'
           WHEN 'm' THEN 'materialized view'
           WHEN 'p' THEN 'partitioned table'
           ELSE c.relkind::text
       END                                       AS kind,
       c.reltuples::bigint                        AS estimated_rows,
       pg_relation_size(c.oid)                    AS size_bytes,
       pg_size_pretty(pg_relation_size(c.oid))    AS size
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'i', 'm', 'p')
  AND n.nspname NOT LIKE 'pg\_%%'
  AND n.nspname <> 'information_schema'
  AND c.relpersistence <> 't'
{% if object_name %}
  AND c.relname LIKE %(object_name)s
{% endif %}
ORDER BY size_bytes DESC
LIMIT 32;
