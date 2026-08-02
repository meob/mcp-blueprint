SELECT schemaname                     AS schema,
       relname                        AS name,
       n_live_tup                     AS estimated_rows
FROM pg_stat_user_tables
{% if min_rows is not none %}
WHERE n_live_tup >= %(min_rows)s
{% endif %}
ORDER BY n_live_tup DESC
LIMIT %(limit)s;
