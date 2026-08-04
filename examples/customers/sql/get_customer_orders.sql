SELECT o.order_id,
       o.status,
       o.total_amount,
       o.created_at,
       o.estimated_delivery,
       o.estimated_delivery IS NOT NULL
           AND o.estimated_delivery < CURRENT_DATE AS is_overdue
FROM orders o
WHERE o.customer_id = %(customer_id)s
{% if status %}
  AND o.status = %(status)s
{% endif %}
ORDER BY o.created_at DESC
LIMIT 50;
