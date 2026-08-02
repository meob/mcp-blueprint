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
           CHANNEL_NAME AS name,
           CASE WHEN SERVICE_STATE = 'ON' THEN 'running' ELSE 'stopped' END AS state,
           NULL AS lag_seconds,
           NULL AS lag_bytes,
           COALESCE(LAST_ERROR_MESSAGE, '') AS detail
    FROM performance_schema.replication_connection_status
) AS b
ORDER BY component, lag_seconds DESC
LIMIT 100;
