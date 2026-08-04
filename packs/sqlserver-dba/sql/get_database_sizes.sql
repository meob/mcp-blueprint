SELECT d.name AS name,
       SUM(f.size * 8192) AS size_bytes,
       CONVERT(decimal(18,1), SUM(f.size * 8.0 / 1024)) AS size_mb,
       d.state_desc AS state,
       d.recovery_model_desc AS recovery_model,
       d.compatibility_level AS compatibility_level
FROM sys.databases d
JOIN sys.master_files f ON d.database_id = f.database_id
GROUP BY d.name, d.state_desc, d.recovery_model_desc, d.compatibility_level
ORDER BY size_bytes DESC
