SELECT COALESCE(wait_event_type, 'idle')            AS wait_event_type,
       COALESCE(wait_event, 'no wait')              AS wait_event,
       count(*)                                     AS sessions
FROM pg_stat_activity
{% if database %}
WHERE datname = %(database)s
{% endif %}
GROUP BY wait_event_type, wait_event
ORDER BY sessions DESC;
