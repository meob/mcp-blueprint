SELECT datname                                    AS database,
       pid,
       usename                                    AS user,
       application_name,
       client_addr,
       wait_event_type,
       wait_event,
       query,
       round(extract(epoch FROM (now() - query_start))) AS running_seconds
FROM pg_stat_activity
WHERE state = 'active'
{% if database %}
  AND datname = %(database)s
{% endif %}
ORDER BY query_start;
