SELECT client_addr                                    AS client,
       state,
       sync_state,
       sent_lsn,
       write_lsn,
       flush_lsn,
       replay_lsn,
       round(extract(epoch FROM (now() - reply_time)))    AS replay_lag_seconds,
       pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn)   AS replay_lag_bytes
FROM pg_stat_replication
ORDER BY client_addr;
