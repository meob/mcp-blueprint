SELECT f.film_id,
       f.title,
       f.release_year,
       f.rating::text                          AS rating,
       ra.label                                AS rating_label,
       ra.min_age,
       f.length,
       f.rental_rate,
       COUNT(DISTINCT rl.rental_id)            AS popularity,
       COUNT(DISTINCT i.inventory_id) FILTER (
           WHERE NOT EXISTS (
               SELECT 1
               FROM rental r2
               WHERE r2.inventory_id = i.inventory_id
                 AND r2.return_date IS NULL
           )
       )                                       AS available_copies
FROM film f
CROSS JOIN LATERAL (
    SELECT CASE f.rating
               WHEN 'G'     THEN 'G - suitable for all ages'
               WHEN 'PG'    THEN 'PG - parental guidance suggested'
               WHEN 'PG-13' THEN 'PG-13 - under 17 requires accompanying parent or guardian'
               WHEN 'R'     THEN 'R - under 17 requires accompanying adult'
               WHEN 'NC-17' THEN 'NC-17 - adults only'
               ELSE f.rating::text
           END                                 AS label,
           CASE f.rating
               WHEN 'G'     THEN 0
               WHEN 'PG'    THEN 10
               WHEN 'PG-13' THEN 13
               WHEN 'R'     THEN 17
               WHEN 'NC-17' THEN 18
               ELSE 0
           END                                 AS min_age
) ra
LEFT JOIN inventory i ON i.film_id = f.film_id
LEFT JOIN rental rl ON rl.inventory_id = i.inventory_id
WHERE 1 = 1
{% if title %}
  AND f.title ILIKE '%%' || %(title)s || '%%'
{% endif %}
{% if category %}
  AND EXISTS (
      SELECT 1
      FROM film_category fc
      JOIN category c ON c.category_id = fc.category_id
      WHERE fc.film_id = f.film_id
        AND c.name = %(category)s
  )
{% endif %}
{% if rating %}
  AND f.rating::text = %(rating)s
{% endif %}
GROUP BY f.film_id, f.title, f.release_year, f.rating, f.length, f.rental_rate,
         ra.label, ra.min_age
ORDER BY popularity DESC, f.title ASC
LIMIT 20;
