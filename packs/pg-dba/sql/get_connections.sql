SELECT datname                                    AS database,
       pid,
       usename                                    AS user,
       application_name,
       client_addr,
       state,
       wait_event_type,
       wait_event,
       round(extract(epoch FROM (now() - backend_start))) AS backend_seconds
FROM pg_stat_activity
{% if database %}
WHERE datname = %(database)s
{% endif %}
ORDER BY backend_start;
