SELECT c.customer_id,
       c.first_name,
       c.last_name,
       c.email,
       c.activebool AS active,
       a.phone,
       ci.city,
       c.store_id
FROM customer c
JOIN address a ON a.address_id = c.address_id
JOIN city ci ON ci.city_id = a.city_id
WHERE c.first_name ILIKE '%%' || %(name)s || '%%'
   OR c.last_name ILIKE '%%' || %(name)s || '%%'
ORDER BY c.last_name, c.first_name
LIMIT 20;
