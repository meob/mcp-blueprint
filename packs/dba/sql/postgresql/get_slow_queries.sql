SELECT left(query, 200) AS query,
       calls,
       round(total_exec_time)              AS total_ms,
       round(mean_exec_time::numeric, 1)     AS mean_ms,
       round(max_exec_time)                AS max_ms,
       rows,
       round(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 1) AS cache_hit_pct,
       pg_get_userbyid(userid)             AS user,
       datname                             AS database
FROM pg_stat_statements
LEFT JOIN pg_database ON pg_database.oid = dbid
ORDER BY total_exec_time DESC
LIMIT 30;
