SELECT version() AS version,
       toInt32(value) AS version_number,
       version() AS full_version
FROM system.metrics
WHERE metric = 'VersionInteger'
