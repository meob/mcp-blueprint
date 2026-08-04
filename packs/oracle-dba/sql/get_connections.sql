SELECT s.sid AS id,
       s.username AS "user",
       s.osuser AS os_user,
       s.program AS program,
       s.status AS state,
       s.type AS type,
       TO_CHAR(s.logon_time, 'YYYY-MM-DD HH24:MI:SS') AS logon,
       ROUND((SYSDATE - s.logon_time) * 86400) AS duration_seconds,
       ROUND(s.last_call_et) AS last_call_seconds,
       s.sql_id AS sql_id,
       (SELECT SUBSTR(REPLACE(REPLACE(q.sql_text, CHR(10), ' '), CHR(13), ' '), 1, 200)
          FROM gv$sql q
         WHERE q.address = s.sql_address
           AND q.inst_id = s.inst_id
         FETCH FIRST 1 ROWS ONLY) AS current_query
FROM gv$session s
WHERE s.type = 'USER'
ORDER BY s.sid
FETCH FIRST 100 ROWS ONLY
