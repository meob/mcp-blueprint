SELECT substring(query, 1, 200) AS query,
       user AS schema,
       count() AS calls,
       sum(query_duration_ms) AS total_ms,
       round(avg(query_duration_ms), 1) AS mean_ms,
       max(query_duration_ms) AS max_ms
FROM system.query_log
WHERE event_time > now() - interval 7 day
  AND type = 2
GROUP BY query, user
ORDER BY total_ms DESC
LIMIT 30
