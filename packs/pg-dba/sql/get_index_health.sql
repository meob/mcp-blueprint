SELECT * FROM (
    SELECT 'invalid' AS component,
           n.nspname || '.' || c.relname AS table_name,
           i.relname AS name,
           'invalid index' AS detail,
           0::bigint AS metric
    FROM pg_index ix
    JOIN pg_class c ON c.oid = ix.indrelid
    JOIN pg_class i ON i.oid = ix.indexrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT ix.indisvalid
      AND c.relpersistence <> 't'
      AND n.nspname NOT LIKE 'pg\_%'
    ORDER BY i.relname
    LIMIT 20
) AS a
UNION ALL
SELECT * FROM (
    SELECT 'unused' AS component,
           s.schemaname || '.' || s.relname AS table_name,
           s.indexrelname AS name,
           pg_relation_size(s.indexrelid) || ' bytes' AS detail,
           pg_relation_size(s.indexrelid) AS metric
    FROM pg_stat_user_indexes s
    JOIN pg_index ix ON ix.indexrelid = s.indexrelid
    WHERE s.idx_scan = 0
      AND NOT ix.indisunique
      AND pg_relation_size(s.indexrelid) > 1048576
    ORDER BY metric DESC
    LIMIT 20
) AS b
UNION ALL
SELECT * FROM (
    SELECT 'missing_fk_index' AS component,
           n.nspname || '.' || c.relname AS table_name,
           con.conname AS name,
           'foreign key without leading-column index' AS detail,
           0::bigint AS metric
    FROM pg_constraint con
    JOIN pg_class c ON c.oid = con.conrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE con.contype = 'f'
      AND NOT EXISTS (
          SELECT 1
          FROM pg_index ix
          WHERE ix.indrelid = con.conrelid
            AND (ix.indkey::int2[])[0:cardinality(con.conkey) - 1] @> con.conkey
            AND 0::int2 <> ALL((ix.indkey::int2[])[0:cardinality(con.conkey) - 1])
      )
    ORDER BY n.nspname, c.relname
    LIMIT 20
) AS c
ORDER BY component, metric DESC
LIMIT 100;
