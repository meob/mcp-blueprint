SELECT pid,
       datname                                                   AS database,
       usename                                                   AS user,
       client_addr,
       to_char(backend_start, 'YYYY-MM-DD HH24:MI:SS')           AS session_start,
       state,
       to_char(query_start, 'YYYY-MM-DD HH24:MI:SS')             AS query_start,
       round(extract(epoch FROM now() - query_start)::numeric, 1) AS duration_seconds,
       backend_type,
       application_name                                          AS application,
       left(replace(query, chr(10), ' '), 200)                   AS current_query
FROM pg_stat_activity
WHERE pid <> pg_backend_pid()
ORDER BY state, query_start, pid;
