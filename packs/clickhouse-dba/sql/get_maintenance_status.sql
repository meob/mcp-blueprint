SELECT * FROM (
    SELECT 'detached_parts' AS component,
           concat(database, '.', table) AS name,
           reason AS detail,
           toInt64(count()) AS metric
    FROM system.detached_parts
    GROUP BY database, table, reason
    UNION ALL
    SELECT 'running_mutations',
           concat(database, '.', table),
           substring(command, 1, 100),
           toInt64(parts_to_do)
    FROM system.mutations
    WHERE is_done = 0
) x
ORDER BY component, name
LIMIT 20
