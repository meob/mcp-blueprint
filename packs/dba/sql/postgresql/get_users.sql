SELECT rolname                                AS role,
       rolsuper                              AS superuser,
       rolcanlogin                           AS can_login,
       rolreplication                        AS replication,
       rolcreatedb                           AS create_db,
       rolinherit                            AS inherit,
       rolconnlimit                          AS connection_limit,
       COALESCE(rolvaliduntil::text, 'never') AS valid_until
FROM pg_roles
ORDER BY rolname
LIMIT 200;
