SELECT datname                                    AS database,
       pid,
       usename                                    AS user,
       application_name,
       state,
       wait_event_type,
       wait_event,
       left(query, 200)                           AS query,
       round(extract(epoch FROM (now() - query_start))) AS running_seconds
FROM pg_stat_activity
WHERE query_start IS NOT NULL
  AND extract(epoch FROM (now() - query_start)) >= %(min_seconds)s
{% if database %}
  AND datname = %(database)s
{% endif %}
ORDER BY running_seconds DESC;
