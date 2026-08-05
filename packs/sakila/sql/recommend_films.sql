{% if customer_name %}
WITH matches AS (
    SELECT c.customer_id
    FROM customer c
    WHERE c.first_name ILIKE '%%' || %(customer_name)s || '%%'
       OR c.last_name ILIKE '%%' || %(customer_name)s || '%%'
       OR (c.first_name || ' ' || c.last_name) ILIKE '%%' || %(customer_name)s || '%%'
)
{% endif %}
SELECT f.film_id,
       f.title,
       f.rating::text                                                       AS rating,
       f.length,
       COUNT(DISTINCT rl.rental_id)                                        AS popularity,
       COUNT(DISTINCT i.inventory_id) FILTER (
           WHERE NOT EXISTS (
               SELECT 1
               FROM rental r2
               WHERE r2.inventory_id = i.inventory_id
                 AND r2.return_date IS NULL
           )
       )                                                                    AS available_copies
FROM film f
LEFT JOIN inventory i ON i.film_id = f.film_id
LEFT JOIN rental rl ON rl.inventory_id = i.inventory_id
WHERE 1 = 1
{% if category %}
  AND (
      (
          LOWER(%(category)s) IN ('g', 'pg', 'pg-13', 'r', 'nc-17')
          AND f.rating::text = %(category)s
      )
      OR
      (
          LOWER(%(category)s) NOT IN ('g', 'pg', 'pg-13', 'r', 'nc-17')
          AND (
              NOT EXISTS (
                  SELECT 1
                  FROM (
                      VALUES
                          ('action', 'Action'),
                          ('animation', 'Animation'),
                          ('children', 'Children'),
                          ('classics', 'Classics'),
                          ('comedy', 'Comedy'),
                          ('documentary', 'Documentary'),
                          ('drama', 'Drama'),
                          ('family', 'Family'),
                          ('foreign', 'Foreign'),
                          ('games', 'Games'),
                          ('horror', 'Horror'),
                          ('music', 'Music'),
                          ('new', 'New'),
                          ('sci-fi', 'Sci-Fi'),
                          ('scifi', 'Sci-Fi'),
                          ('science fiction', 'Sci-Fi'),
                          ('science-fiction', 'Sci-Fi'),
                          ('sports', 'Sports'),
                          ('travel', 'Travel')
                  ) AS cat(synonym, name)
                  WHERE synonym = LOWER(%(category)s)
              )
              OR EXISTS (
                  SELECT 1
                  FROM film_category fc
                  JOIN category c ON c.category_id = fc.category_id
                  WHERE fc.film_id = f.film_id
                    AND c.name IN (
                        SELECT name
                        FROM (
                            VALUES
                                ('action', 'Action'),
                                ('animation', 'Animation'),
                                ('children', 'Children'),
                                ('classics', 'Classics'),
                                ('comedy', 'Comedy'),
                                ('documentary', 'Documentary'),
                                ('drama', 'Drama'),
                                ('family', 'Family'),
                                ('foreign', 'Foreign'),
                                ('games', 'Games'),
                                ('horror', 'Horror'),
                                ('music', 'Music'),
                                ('new', 'New'),
                                ('sci-fi', 'Sci-Fi'),
                                ('scifi', 'Sci-Fi'),
                                ('science fiction', 'Sci-Fi'),
                                ('science-fiction', 'Sci-Fi'),
                                ('sports', 'Sports'),
                                ('travel', 'Travel')
                        ) AS cat(synonym, name)
                        WHERE synonym = LOWER(%(category)s)
                    )
              )
          )
      )
  )
{% endif %}
{% if rating %}
  AND (
      LOWER(%(rating)s) NOT IN ('g', 'pg', 'pg-13', 'r', 'nc-17')
      OR f.rating::text = %(rating)s
  )
{% endif %}
{% if customer_name %}
  AND NOT EXISTS (
      SELECT 1
      FROM rental r3
      JOIN inventory i3 ON i3.inventory_id = r3.inventory_id
      WHERE i3.film_id = f.film_id
        AND r3.customer_id IN (SELECT customer_id FROM matches)
  )
{% endif %}
GROUP BY f.film_id, f.title, f.rating, f.length
{% if in_stock_only %}
  HAVING COUNT(DISTINCT i.inventory_id) FILTER (
      WHERE NOT EXISTS (
          SELECT 1
          FROM rental r2
          WHERE r2.inventory_id = i.inventory_id
            AND r2.return_date IS NULL
      )
  ) > 0
{% endif %}
ORDER BY popularity DESC, f.title ASC
LIMIT {% if count is undefined or count is none %}5{% else %}%(count)s{% endif %};
