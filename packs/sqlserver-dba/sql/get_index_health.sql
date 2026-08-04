SELECT TOP 20
       CONVERT(decimal(18,2), migs.user_seeks * migs.avg_total_user_cost * (migs.avg_user_impact * 0.01)) AS advantage,
       mid.statement AS db_schema_table,
       mid.equality_columns AS equality_columns,
       mid.inequality_columns AS inequality_columns,
       migs.user_seeks AS user_seeks,
       migs.last_user_seek AS last_user_seek
FROM sys.dm_db_missing_index_group_stats migs
INNER JOIN sys.dm_db_missing_index_groups mig ON migs.group_handle = mig.index_group_handle
INNER JOIN sys.dm_db_missing_index_details mid ON mig.index_handle = mid.index_handle
WHERE mid.database_id = DB_ID()
ORDER BY advantage DESC
