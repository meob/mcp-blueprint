SELECT datname                          AS database,
       pg_database_size(datname)        AS size_bytes
FROM pg_database
{% if database %}
WHERE datname = %(database)s
{% endif %}
ORDER BY size_bytes DESC;
