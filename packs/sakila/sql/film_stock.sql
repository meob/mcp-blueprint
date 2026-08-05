SELECT f.film_id,
       f.title,
       f.rating::text                                                       AS rating,
       f.length,
       s.store_id,
       COUNT(i.inventory_id)                                                AS total_copies,
       COUNT(i.inventory_id) FILTER (
           WHERE NOT EXISTS (
               SELECT 1
               FROM rental r
               WHERE r.inventory_id = i.inventory_id
                 AND r.return_date IS NULL
           )
       )                                                                    AS available
FROM film f
JOIN inventory i ON i.film_id = f.film_id
JOIN store s ON s.store_id = i.store_id
WHERE f.title ILIKE '%%' || %(title)s || '%%'
{% if store_id %}
  AND s.store_id = %(store_id)s
{% endif %}
GROUP BY f.film_id, f.title, f.rating, f.length, s.store_id
ORDER BY f.film_id, s.store_id
LIMIT 50;
