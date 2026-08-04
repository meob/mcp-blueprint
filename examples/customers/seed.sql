INSERT INTO customers (full_name, email, city) VALUES
    ('Marta Bianchi',  'marta.bianchi@example.com',   'Rome'),
    ('Luca Rossi',     'luca.rossi@example.com',      'Milan'),
    ('Anna Verdi',     'anna.verdi@example.com',      'Turin'),
    ('Paolo Esposito', 'paolo.esposito@example.com',  'Naples'),
    ('Giulia Romano',  'giulia.romano@example.com',   'Rome');

INSERT INTO orders (customer_id, status, total_amount, created_at, estimated_delivery) VALUES
    (1, 'delivered', 89.90, now() - interval '30 days', CURRENT_DATE - 26),
    (1, 'shipped',   42.50, now() - interval '3 days',  CURRENT_DATE - 1),
    (2, 'pending',   120.00, now() - interval '1 day',  CURRENT_DATE + 4),
    (2, 'delivered', 25.00, now() - interval '12 days', CURRENT_DATE - 9),
    (3, 'cancelled', 60.00, now() - interval '8 days',  CURRENT_DATE - 5),
    (3, 'pending',   15.75, now() - interval '5 hours', CURRENT_DATE + 2),
    (4, 'pending',   33.20, now() - interval '6 hours', CURRENT_DATE + 1),
    (4, 'pending',   71.10, now() - interval '2 hours', CURRENT_DATE + 3),
    (5, 'shipped',   95.00, now() - interval '10 days', CURRENT_DATE - 8);
