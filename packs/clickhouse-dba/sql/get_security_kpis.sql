SELECT * FROM (
    SELECT 'superuser_login_roles' AS kpi_name,
           (SELECT count(DISTINCT user_name) FROM system.grants WHERE access_type = 'ALL') AS current_value,
           'roles' AS unit,
           '<= 1' AS suggested_threshold,
           if((SELECT count(DISTINCT user_name) FROM system.grants WHERE access_type = 'ALL') > 1, 'warning', 'ok') AS status
    UNION ALL
    SELECT 'login_roles', count(), 'roles', '< 100',
           if(count() >= 100, 'warning', 'ok')
    FROM system.users
    UNION ALL
    SELECT 'accounts_without_password', count(), 'accounts', '= 0',
           if(count() > 0, 'warning', 'ok')
    FROM system.users
    WHERE auth_type = 'no_password'
    UNION ALL
    SELECT 'ldap_users', count(), 'accounts', '< 10',
           if(count() >= 10, 'warning', 'ok')
    FROM system.users
    WHERE auth_type = 'ldap'
) kpi
ORDER BY kpi_name
