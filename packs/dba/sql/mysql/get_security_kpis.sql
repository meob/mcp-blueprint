SELECT * FROM (
    SELECT 'superuser_login_roles' AS kpi_name,
           (SELECT COUNT(*) FROM mysql.user WHERE Super_priv = 'Y') AS current_value,
           'roles' AS unit,
           '<= 1' AS suggested_threshold,
           CASE WHEN (SELECT COUNT(*) FROM mysql.user WHERE Super_priv = 'Y') > 1 THEN 'warning' ELSE 'ok' END AS status
    UNION ALL
    SELECT 'login_roles', COUNT(*), 'roles', '< 100',
           CASE WHEN COUNT(*) >= 100 THEN 'warning' ELSE 'ok' END
    FROM mysql.user
    UNION ALL
    SELECT 'expired_roles', COUNT(*), 'roles', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'error' ELSE 'ok' END
    FROM mysql.user
    WHERE password_expired = 'Y'
    UNION ALL
    SELECT 'accounts_without_password', COUNT(*), 'accounts', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM mysql.user
    WHERE authentication_string = ''
      AND plugin NOT IN ('auth_socket', 'unix_socket')
    UNION ALL
    SELECT 'anonymous_accounts', COUNT(*), 'accounts', '= 0',
           CASE WHEN COUNT(*) > 0 THEN 'warning' ELSE 'ok' END
    FROM mysql.user
    WHERE User = ''
) kpi
ORDER BY kpi_name;
