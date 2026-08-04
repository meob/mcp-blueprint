WITH stats AS (
    SELECT count(*) FILTER (WHERE status = 'pending') AS pending_orders,
           count(*) FILTER (WHERE status = 'shipped'
                              AND estimated_delivery < CURRENT_DATE) AS overdue_shipments,
           count(*) FILTER (WHERE status = 'cancelled') AS cancelled_orders,
           count(*)                                   AS total_orders,
           COALESCE(sum(total_amount) FILTER (WHERE status <> 'cancelled'), 0) AS open_order_value,
           COALESCE(avg(total_amount), 0)             AS average_order_value
    FROM orders
)
SELECT * FROM (
    SELECT 'pending_orders' AS kpi_name,
           pending_orders::text AS current_value,
           'orders' AS unit,
           '< 10' AS suggested_threshold,
           CASE WHEN pending_orders >= 10 THEN 'warning' ELSE 'ok' END AS status
    FROM stats
    UNION ALL
    SELECT 'overdue_shipments', overdue_shipments::text, 'orders', '= 0',
           CASE WHEN overdue_shipments > 0 THEN 'error' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'cancelled_rate_pct',
           round(100.0 * cancelled_orders / NULLIF(total_orders, 0), 1)::text,
           '%', '< 5',
           CASE WHEN 100.0 * cancelled_orders / NULLIF(total_orders, 0) >= 5
                THEN 'warning' ELSE 'ok' END
    FROM stats
    UNION ALL
    SELECT 'open_order_value', round(open_order_value, 2)::text, 'currency', 'n/a', 'ok'
    FROM stats
    UNION ALL
    SELECT 'average_order_value', round(average_order_value, 2)::text, 'currency', 'n/a', 'ok'
    FROM stats
) kpi
ORDER BY kpi_name;
