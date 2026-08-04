SELECT c.customer_id,
       c.full_name,
       c.email,
       c.city,
       COUNT(o.order_id)                  AS total_orders,
       COALESCE(SUM(o.total_amount), 0)   AS total_spent,
       CASE
           WHEN COUNT(o.order_id) = 0 THEN 0
           ELSE round(SUM(o.total_amount) / COUNT(o.order_id), 2)
       END                                AS average_order_value,
       MAX(o.created_at)                  AS last_order_date
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE c.customer_id = %(customer_id)s
GROUP BY c.customer_id, c.full_name, c.email, c.city;
