SELECT * FROM (
    SELECT 'oldest_vacuum' AS component,
           schemaname || '.' || relname AS name,
           COALESCE(last_vacuum, last_autovacuum)::text AS detail,
           extract(epoch FROM (now() - COALESCE(last_vacuum, last_autovacuum)))::bigint AS metric
    FROM pg_stat_user_tables
    WHERE last_vacuum IS NOT NULL OR last_autovacuum IS NOT NULL
    ORDER BY COALESCE(last_vacuum, last_autovacuum) ASC
    LIMIT 10
) AS a
UNION ALL
SELECT * FROM (
    SELECT 'never_vacuumed' AS component,
           s.schemaname || '.' || s.relname AS name,
           'no vacuum recorded' AS detail,
           COALESCE(c.reltuples::bigint, 0) AS metric
    FROM pg_stat_user_tables s
    JOIN pg_class c ON c.oid = s.relid
    WHERE s.last_vacuum IS NULL AND s.last_autovacuum IS NULL AND c.reltuples > 100
    ORDER BY c.reltuples DESC
    LIMIT 10
) AS b
UNION ALL
SELECT * FROM (
    SELECT 'active_maintenance' AS component,
           pid::text AS name,
           left(query, 100) AS detail,
           extract(epoch FROM (now() - query_start))::bigint AS metric
    FROM pg_stat_activity
    WHERE state <> 'idle'
      AND (query ILIKE 'vacuum%' OR query ILIKE 'analyze%'
           OR query ILIKE 'reindex%' OR query ILIKE 'cluster%')
    ORDER BY query_start ASC
    LIMIT 10
) AS c
UNION ALL
SELECT * FROM (
    SELECT 'high_dead_tuples' AS component,
           schemaname || '.' || relname AS name,
           n_dead_tup || ' dead, ' || round(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 1) || '%' AS detail,
           n_dead_tup AS metric
    FROM pg_stat_all_tables
    WHERE n_dead_tup > 1000 AND n_dead_tup > n_live_tup * 0.05
    ORDER BY n_dead_tup DESC
    LIMIT 10
) AS d
UNION ALL
SELECT * FROM (
    SELECT 'xid_wraparound' AS component,
           datname AS name,
           round(100.0 * age(datfrozenxid)
                 / GREATEST(current_setting('autovacuum_freeze_max_age')::int, 1), 1) || '%' AS detail,
           age(datfrozenxid) AS metric
    FROM pg_database
    WHERE datallowconn
    ORDER BY age(datfrozenxid) DESC
    LIMIT 10
) AS e
ORDER BY component, metric DESC
LIMIT 100;
