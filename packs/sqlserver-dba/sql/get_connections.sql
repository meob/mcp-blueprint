SELECT TOP 100
       s.session_id AS id,
       s.login_name AS [user],
       s.host_name AS host,
       s.program_name AS program,
       r.status AS state,
       s.status AS session_state,
       r.command AS current_query,
       s.cpu_time AS cpu_ms,
       s.memory_usage AS memory_8k_pages,
       CONVERT(varchar, s.login_time, 120) AS login_time,
       DATEDIFF(second, s.login_time, GETDATE()) AS duration_seconds
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
WHERE s.session_id <> @@SPID
  AND s.is_user_process = 1
ORDER BY s.session_id
