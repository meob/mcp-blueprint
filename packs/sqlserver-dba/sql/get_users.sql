SELECT name AS role,
       type_desc AS type,
       default_database_name AS default_database,
       is_disabled AS is_disabled,
       is_policy_checked AS is_policy_checked,
       is_expiration_checked AS is_expiration_checked,
       CONVERT(varchar, create_date, 120) AS created,
       LOGINPROPERTY(name, 'DaysUntilExpiration') AS days_until_expiration
FROM sys.sql_logins
ORDER BY name
