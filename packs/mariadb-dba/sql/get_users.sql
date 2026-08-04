SELECT User AS role,
       Host AS host,
       CASE WHEN authentication_string <> '' THEN 'yes' ELSE 'no' END AS has_password,
       CASE WHEN Super_priv = 'Y' THEN true ELSE false END AS superuser,
       CASE WHEN Create_priv = 'Y' THEN true ELSE false END AS create_db,
       CASE WHEN is_role = 'Y' THEN true ELSE false END AS is_role,
       CASE WHEN password_expired = 'Y' THEN true ELSE false END AS password_expired
FROM mysql.user
ORDER BY role, Host
LIMIT 200;
