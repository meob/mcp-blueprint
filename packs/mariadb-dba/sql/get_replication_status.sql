SELECT * FROM (
    SELECT 'instance' AS component,
           @@hostname AS name,
           CASE WHEN @@read_only = 0 THEN 'primary' ELSE 'standby' END AS state,
           NULL AS lag_seconds,
           NULL AS lag_bytes,
           'role derived from read_only' AS detail
) AS a
UNION ALL
SELECT * FROM (
    SELECT 'channel' AS component,
           a.CHANNEL_NAME AS name,
           CASE WHEN a.SERVICE_STATE = 'ON' THEN 'running' ELSE 'stopped' END AS state,
           a.REMAINING_DELAY AS lag_seconds,
           NULL AS lag_bytes,
           CONCAT(COALESCE(c.HOST, ''), ':', COALESCE(c.PORT, '')) AS detail
    FROM performance_schema.replication_applier_status a
    LEFT JOIN performance_schema.replication_connection_configuration c
           ON a.CHANNEL_NAME = c.CHANNEL_NAME
) AS b
ORDER BY component, lag_seconds DESC
LIMIT 100;
