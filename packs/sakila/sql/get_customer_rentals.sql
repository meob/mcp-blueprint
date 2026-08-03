SELECT r.rental_id,
       f.title,
       r.rental_date,
       r.return_date,
       CASE
           WHEN r.return_date IS NULL
                AND r.rental_date + f.rental_duration * INTERVAL '1 day' < CURRENT_TIMESTAMP
               THEN 'overdue'
           WHEN r.return_date IS NULL THEN 'active'
           ELSE 'returned'
       END AS status
FROM rental r
JOIN inventory i ON i.inventory_id = r.inventory_id
JOIN film f ON f.film_id = i.film_id
WHERE r.customer_id = %(customer_id)s
ORDER BY r.rental_date DESC
LIMIT 50;
