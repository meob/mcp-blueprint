SELECT id,
       `user`,
       `host`,
       `db`,
       `command`,
       `time`,
       `state`,
       LEFT(REPLACE(INFO, '\n', ' '), 200) AS current_query
FROM information_schema.processlist
WHERE id <> CONNECTION_ID()
ORDER BY id;
