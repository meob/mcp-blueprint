WITH matches AS (
    SELECT c.customer_id
    FROM customer c
    WHERE c.first_name ILIKE '%%' || %(customer_name)s || '%%'
       OR c.last_name ILIKE '%%' || %(customer_name)s || '%%'
       OR (c.first_name || ' ' || c.last_name) ILIKE '%%' || %(customer_name)s || '%%'
)
SELECT c.customer_id,
       c.first_name,
       c.last_name,
       c.email,
       ci.city,
       c.store_id,
       (SELECT count(*)
        FROM rental r0
        WHERE r0.customer_id = c.customer_id)::int                          AS total_rentals,
       (SELECT count(*)
        FROM rental r1
        WHERE r1.customer_id = c.customer_id
          AND r1.return_date IS NULL)::int                                  AS open_rentals,
       (SELECT count(*)::int
        FROM rental r2
        JOIN inventory i2 ON i2.inventory_id = r2.inventory_id
        JOIN film f2 ON f2.film_id = i2.film_id
        WHERE r2.customer_id = c.customer_id
          AND r2.return_date IS NULL
          AND r2.rental_date + f2.rental_duration * INTERVAL '1 day' < CURRENT_TIMESTAMP) AS overdue_rentals,
       CASE
           WHEN (
               SELECT count(*)::int
               FROM rental r4
               JOIN inventory i4 ON i4.inventory_id = r4.inventory_id
               JOIN film f4 ON f4.film_id = i4.film_id
               WHERE r4.customer_id = c.customer_id
                 AND r4.return_date IS NULL
                 AND r4.rental_date + f4.rental_duration * INTERVAL '1 day' < CURRENT_TIMESTAMP
           ) > 0 THEN 'HAS OVERDUE'
           ELSE 'GOOD STANDING'
       END                                                                  AS standing,
       (SELECT COALESCE(string_agg(
                   f.title
                   || CASE
                          WHEN r.rental_date + f.rental_duration * INTERVAL '1 day' < CURRENT_TIMESTAMP
                            THEN ' (OVERDUE)'
                          ELSE ''
                      END,
                   ', ' ORDER BY r.rental_date DESC), 'NONE')
        FROM rental r
        JOIN inventory i ON i.inventory_id = r.inventory_id
        JOIN film f ON f.film_id = i.film_id
        WHERE r.customer_id = c.customer_id
          AND r.return_date IS NULL)                                       AS open_films
FROM customer c
JOIN address a ON a.address_id = c.address_id
JOIN city ci ON ci.city_id = a.city_id
WHERE c.customer_id IN (SELECT customer_id FROM matches)
ORDER BY c.last_name, c.first_name
LIMIT 20;
