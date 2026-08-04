SELECT 'backup' AS component,
       d.name AS name,
       ISNULL(CONVERT(varchar, MAX(b.backup_finish_date), 120), 'no backup') AS detail,
       NULL AS metric
FROM sys.databases d
LEFT JOIN msdb.dbo.backupset b ON d.name = b.database_name AND b.type = 'D'
GROUP BY d.name
UNION ALL
SELECT 'log_usage',
       db_name(),
       CONCAT(CONVERT(varchar, CONVERT(decimal(5,1), used_log_space_in_percent)), ' % used'),
       total_log_size_in_bytes
FROM sys.dm_db_log_space_usage
ORDER BY component, name
