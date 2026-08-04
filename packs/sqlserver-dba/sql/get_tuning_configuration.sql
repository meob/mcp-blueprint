SELECT name,
       CONVERT(nvarchar(128), value) AS value,
       NULL AS unit,
       'instance' AS context,
       CASE WHEN value_in_use <> value THEN 'modified' ELSE 'default' END AS category,
       CONVERT(nvarchar(128), value_in_use) AS value_in_use,
       is_dynamic AS is_dynamic
FROM sys.configurations
WHERE name IN ('max server memory (MB)', 'min server memory (MB)', 'cost threshold for parallelism',
               'max degree of parallelism', 'recovery interval', 'optimize for ad hoc workloads',
               'clr enabled', 'backup compression default', 'user connections', 'max worker threads',
               'remote query timeout', 'remote login timeout', 'fill factor (%)', 'max full-text crawl range')
ORDER BY name
