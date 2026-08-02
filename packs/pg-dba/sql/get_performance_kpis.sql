WITH stats AS (
    SELECT 100.0 * sum(blks_hit) / NULLIF(sum(blks_hit) + sum(blks_read), 0) AS cache_hit_pct
    FROM pg_stat_database
    WHERE datname = current_database()
),
index_cache AS (
    SELECT 100.0 * sum(idx_blks_hit) / NULLIF(sum(idx_blks_hit) + sum(idx_blks_read), 0) AS index_cache_hit_pct
    FROM pg_statio_user_indexes
),
db_stats AS (
    SELECT xact_commit,
           xact_rollback,
           tup_inserted,
           temp_bytes,
           stats_reset
    FROM pg_stat_database
    WHERE datname = current_database()
),
dead AS (
    SELECT max(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0)) AS max_dead_tuples_pct
    FROM pg_stat_all_tables
    WHERE n_live_tup > 10000 AND n_dead_tup > 0
),
freeze_age AS (
    SELECT max(100.0 * age(relfrozenxid)
               / GREATEST(current_setting('autovacuum_freeze_max_age')::int, 1)) AS autovacuum_freeze_pct
    FROM pg_class
    WHERE relkind IN ('r', 'm', 'p') AND relfrozenxid <> '0'::xid
),
wrap AS (
    SELECT max(100.0 * age(datfrozenxid)
               / GREATEST(current_setting('autovacuum_freeze_max_age')::int, 1)) AS xid_wraparound_pct
    FROM pg_database
    WHERE datallowconn
)
SELECT * FROM (
    SELECT 'cache_hit_ratio_pct' AS kpi_name,
           round(stats.cache_hit_pct, 1)::text AS current_value,
           '%' AS unit,
           '> 95' AS suggested_threshold,
           CASE WHEN stats.cache_hit_pct < 95 THEN 'warning' ELSE 'ok' END AS status
    FROM stats
    UNION ALL
    SELECT 'index_cache_hit_ratio_pct',
           round(index_cache.index_cache_hit_pct, 1)::text,
           '%',
           '> 98',
           CASE WHEN index_cache.index_cache_hit_pct < 98 THEN 'warning' ELSE 'ok' END
    FROM index_cache
    UNION ALL
    SELECT 'rollback_pct',
           round(COALESCE(100.0 * db_stats.xact_rollback / NULLIF(db_stats.xact_commit + db_stats.xact_rollback, 0), 0), 1)::text,
           '%',
           '< 1',
           CASE WHEN COALESCE(100.0 * db_stats.xact_rollback / NULLIF(db_stats.xact_commit + db_stats.xact_rollback, 0), 0) >= 1 THEN 'warning' ELSE 'ok' END
    FROM db_stats
    UNION ALL
    SELECT 'max_dead_tuples_pct',
           round(dead.max_dead_tuples_pct, 1)::text,
           '%',
           '< 20',
           CASE WHEN dead.max_dead_tuples_pct >= 20 THEN 'warning' ELSE 'ok' END
    FROM dead
    UNION ALL
    SELECT 'autovacuum_freeze_pct',
           round(freeze_age.autovacuum_freeze_pct, 1)::text,
           '%',
           '< 95',
           CASE WHEN freeze_age.autovacuum_freeze_pct >= 95 THEN 'warning' ELSE 'ok' END
    FROM freeze_age
    UNION ALL
    SELECT 'xid_wraparound_pct',
           round(wrap.xid_wraparound_pct, 1)::text,
           '%',
           '< 95',
           CASE WHEN wrap.xid_wraparound_pct >= 95 THEN 'error' ELSE 'ok' END
    FROM wrap
    UNION ALL
    SELECT 'temp_bytes_per_hour',
           round(db_stats.temp_bytes * 3600.0 / NULLIF(extract(epoch FROM (now() - db_stats.stats_reset)), 0))::text,
           'bytes',
           '< 1073741824',
           CASE WHEN db_stats.temp_bytes * 3600.0 / NULLIF(extract(epoch FROM (now() - db_stats.stats_reset)), 0) >= 1073741824 THEN 'warning' ELSE 'ok' END
    FROM db_stats
    UNION ALL
    SELECT 'rows_inserted_per_hour',
           round(db_stats.tup_inserted * 3600.0 / NULLIF(extract(epoch FROM (now() - db_stats.stats_reset)), 0))::text,
           'rows',
           '< 1000000',
           CASE WHEN db_stats.tup_inserted * 3600.0 / NULLIF(extract(epoch FROM (now() - db_stats.stats_reset)), 0) >= 1000000 THEN 'warning' ELSE 'ok' END
    FROM db_stats
) kpi
ORDER BY kpi_name;
