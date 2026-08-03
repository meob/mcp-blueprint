SELECT id,
       `user`,
       `host`,
       `db`,
       `command`,
       `time`,
       `state`,
       LEFT(REPLACE(info, '\n', ' '), 200) AS current_query
FROM performance_schema.processlist
WHERE id <> CONNECTION_ID()
ORDER BY id;
