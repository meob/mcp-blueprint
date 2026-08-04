SELECT name AS role,
       auth_type AS auth_type,
       storage AS storage,
       default_roles_all AS default_roles_all,
       host_names AS host_names
FROM system.users
ORDER BY name
LIMIT 200
