WITH matches AS (
    SELECT c.customer_id
    FROM customer c
    WHERE c.first_name ILIKE '%%' || %(customer_name)s || '%%'
       OR c.last_name ILIKE '%%' || %(customer_name)s || '%%'
       OR (c.first_name || ' ' || c.last_name) ILIKE '%%' || %(customer_name)s || '%%'
)
SELECT r.rental_id,
       f.title,
       to_char(r.rental_date, 'YYYY-MM-DD')                                 AS rental_date,
       CASE
           WHEN r.return_date IS NULL
             AND r.rental_date + f.rental_duration * INTERVAL '1 day' < CURRENT_TIMESTAMP THEN 'overdue'
           WHEN r.return_date IS NULL THEN 'active'
           ELSE 'returned'
       END                                                                  AS status
FROM rental r
JOIN inventory i ON i.inventory_id = r.inventory_id
JOIN film f ON f.film_id = i.film_id
WHERE r.customer_id IN (SELECT customer_id FROM matches)
ORDER BY r.rental_date DESC, r.rental_id DESC
LIMIT 25;
