SELECT f.film_id,
       f.title,
       f.description,
       f.release_year,
       f.rating::text                          AS rating,
       ra.label                                AS rating_label,
       ra.min_age,
       f.length,
       f.rental_duration,
       f.rental_rate,
       f.replacement_cost,
       array_to_string(f.special_features, ', ') AS special_features,
       (SELECT string_agg(a.first_name || ' ' || a.last_name, ', ' ORDER BY a.last_name, a.first_name)
        FROM film_actor fa
        JOIN actor a ON a.actor_id = fa.actor_id
        WHERE fa.film_id = f.film_id)          AS actors,
       (SELECT string_agg(c.name, ', ' ORDER BY c.name)
        FROM film_category fc
        JOIN category c ON c.category_id = fc.category_id
        WHERE fc.film_id = f.film_id)          AS categories,
       (SELECT COALESCE(
                   string_agg('Store ' || s.store_id || ': ' || s.available || ' available',
                              ', ' ORDER BY s.store_id),
                   '')
        FROM (
            SELECT inv.store_id,
                   COUNT(inv.inventory_id) - COUNT(rl.rental_id) AS available
            FROM inventory inv
            LEFT JOIN rental rl
                   ON rl.inventory_id = inv.inventory_id
                  AND rl.return_date IS NULL
            WHERE inv.film_id = f.film_id
            GROUP BY inv.store_id
        ) s)                                   AS store_availability
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
WHERE f.film_id = %(film_id)s
LIMIT 1;
