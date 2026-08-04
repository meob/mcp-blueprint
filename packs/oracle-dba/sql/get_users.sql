SELECT username AS role,
       default_tablespace AS default_tablespace,
       temporary_tablespace AS temp_tablespace,
       account_status AS account_status,
       profile AS profile,
       CASE WHEN authentication_type = 'PASSWORD' THEN 'yes' ELSE 'no' END AS has_password,
       TO_CHAR(created, 'YYYY-MM-DD HH24:MI:SS') AS created,
       TO_CHAR(expiry_date, 'YYYY-MM-DD HH24:MI:SS') AS expiry,
       TO_CHAR(last_login, 'YYYY-MM-DD HH24:MI:SS') AS last_login,
       (SELECT COUNT(*)
          FROM dba_role_privs rp
         WHERE rp.grantee = u.username
           AND rp.granted_role IN ('DBA', 'SYSDBA', 'SYSOPER')) AS superuser_roles
FROM dba_users u
ORDER BY username
FETCH FIRST 200 ROWS ONLY
