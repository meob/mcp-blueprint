SELECT LEFT(DIGEST_TEXT, 200) AS `query`,
       COUNT_STAR AS calls,
       ROUND(SUM_TIMER_WAIT / 1000000000) AS total_ms,
       ROUND(AVG_TIMER_WAIT / 1000000, 1) AS mean_ms,
       ROUND(MAX_TIMER_WAIT / 1000000) AS max_ms,
       SCHEMA_NAME AS `database`
FROM performance_schema.events_statements_summary_by_digest
WHERE SCHEMA_NAME IS NOT NULL
ORDER BY SUM_TIMER_WAIT DESC
LIMIT 30;
