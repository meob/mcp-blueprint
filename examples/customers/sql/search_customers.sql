SELECT c.customer_id,
       c.full_name,
       c.email,
       c.city,
       COUNT(o.order_id)                    AS total_orders,
       COALESCE(SUM(o.total_amount), 0)     AS total_spent
FROM customers c
LEFT JOIN orders o ON o.customer_id = c.customer_id
WHERE 1 = 1
{% if name %}
  AND c.full_name ILIKE '%%' || %(name)s || '%%'
{% endif %}
{% if city %}
  AND c.city ILIKE '%%' || %(city)s || '%%'
{% endif %}
GROUP BY c.customer_id, c.full_name, c.email, c.city
ORDER BY c.full_name ASC
LIMIT 20;
