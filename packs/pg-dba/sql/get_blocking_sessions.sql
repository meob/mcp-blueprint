SELECT blocked.pid                                   AS blocked_pid,
       blocked.datname                               AS database,
       blocked.usename                               AS blocked_user,
       left(blocked.query, 200)                      AS blocked_query,
       blocking.pid                                  AS blocking_pid,
       blocking.usename                              AS blocking_user,
       left(blocking.query, 200)                     AS blocking_query,
       round(extract(epoch FROM (now() - blocked.state_change))) AS blocked_seconds
FROM pg_stat_activity AS blocked
JOIN pg_stat_activity AS blocking
  ON blocking.pid = ANY (pg_blocking_pids(blocked.pid))
{% if database %}
WHERE blocked.datname = %(database)s
{% endif %}
ORDER BY blocked_seconds DESC;
