SELECT * FROM (
    SELECT 'superuser_login_roles' AS kpi_name,
           (SELECT COUNT(DISTINCT grantee) FROM dba_role_privs WHERE granted_role IN ('DBA', 'SYSDBA', 'SYSOPER')) AS current_value,
           'roles' AS unit,
           '<= 1' AS suggested_threshold,
           CASE WHEN (SELECT COUNT(DISTINCT grantee) FROM dba_role_privs WHERE granted_role IN ('DBA', 'SYSDBA', 'SYSOPER')) > 1 THEN 'warning' ELSE 'ok' END AS status
    FROM dual
    UNION ALL
    SELECT 'login_roles', COUNT(*), 'roles', '< 100',
           CASE WHEN COUNT(*) >= 100 THEN 'warning' ELSE 'ok' END
    FROM dba_users
    WHERE account_status LIKE 'OPEN%'
    UNION ALL
    SELECT 'expired_roles', COUNT(*), 'roles', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'error' ELSE 'ok' END
    FROM dba_users
    WHERE account_status LIKE 'EXPIRED%'
    UNION ALL
    SELECT 'accounts_without_password', COUNT(*), 'accounts', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM dba_users
    WHERE authentication_type = 'NONE'
) kpi
ORDER BY kpi_name
