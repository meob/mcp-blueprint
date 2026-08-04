SELECT * FROM (
    SELECT 'superuser_login_roles' AS kpi_name,
           (SELECT COUNT(*) FROM sys.server_role_members rm JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id WHERE r.name = 'sysadmin') AS current_value,
           'roles' AS unit,
           '<= 1' AS suggested_threshold,
           CASE WHEN (SELECT COUNT(*) FROM sys.server_role_members rm JOIN sys.server_principals r ON rm.role_principal_id = r.principal_id WHERE r.name = 'sysadmin') > 1 THEN 'warning' ELSE 'ok' END AS status
    UNION ALL
    SELECT 'login_roles', COUNT(*), 'roles', '< 100',
           CASE WHEN COUNT(*) >= 100 THEN 'warning' ELSE 'ok' END
    FROM sys.sql_logins
    UNION ALL
    SELECT 'disabled_logins', COUNT(*), 'logins', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM sys.sql_logins
    WHERE is_disabled = 1
    UNION ALL
    SELECT 'password_policy_not_checked', COUNT(*), 'logins', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM sys.sql_logins
    WHERE is_policy_checked = 0
      AND type = 'S'
) kpi
ORDER BY kpi_name
