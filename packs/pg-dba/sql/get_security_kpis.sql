WITH stats AS (
    SELECT (SELECT count(*) FROM pg_roles WHERE rolcanlogin)               AS login_roles,
           (SELECT count(*) FROM pg_roles WHERE rolcanlogin AND rolsuper) AS superuser_login_roles,
           (SELECT count(*) FROM pg_roles
             WHERE rolcanlogin AND rolvaliduntil IS NOT NULL
               AND rolvaliduntil > now() AND rolvaliduntil < now() + interval '30 days') AS expiring_30d,
           (SELECT count(*) FROM pg_roles
             WHERE rolcanlogin AND rolvaliduntil IS NOT NULL AND rolvaliduntil < now())    AS expired_roles,
           (SELECT count(*) FROM pg_database d
             JOIN pg_roles r ON r.oid = d.datdba
             WHERE NOT r.rolsuper)                                          AS databases_owned_by_non_superuser,
           (SELECT count(*) FROM pg_namespace n
             JOIN pg_roles r ON r.oid = n.nspowner
             WHERE NOT r.rolsuper
               AND n.nspname NOT LIKE 'pg\_%'
               AND n.nspname <> 'information_schema')                       AS schemas_owned_by_non_superuser
)
SELECT * FROM (
    SELECT 'superuser_login_roles' AS kpi_name,
           superuser_login_roles::text AS current_value,
           'roles' AS unit,
           '<= 1' AS suggested_threshold,
           CASE WHEN superuser_login_roles > 1 THEN 'warning' ELSE 'ok' END AS status
    FROM stats
    UNION ALL
    SELECT 'login_roles', login_roles::text, 'roles', '< 100',
           CASE WHEN login_roles >= 100 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'roles_expiring_within_30d', expiring_30d::text, 'roles', '= 0',
           CASE WHEN expiring_30d > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'expired_roles', expired_roles::text, 'roles', '= 0',
           CASE WHEN expired_roles > 0 THEN 'error' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'databases_owned_by_non_superuser', databases_owned_by_non_superuser::text, 'databases', '= 0',
           CASE WHEN databases_owned_by_non_superuser > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'schemas_owned_by_non_superuser', schemas_owned_by_non_superuser::text, 'schemas', '= 0',
           CASE WHEN schemas_owned_by_non_superuser > 0 THEN 'warning' ELSE 'ok' END
    FROM stats
) kpi
ORDER BY kpi_name;
