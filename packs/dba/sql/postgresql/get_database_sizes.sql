SELECT datname                              AS database,
       pg_database_size(datname)            AS size_bytes,
       pg_size_pretty(pg_database_size(datname)) AS size,
       datistemplate                        AS is_template
FROM pg_database
ORDER BY size_bytes DESC
LIMIT 100;
