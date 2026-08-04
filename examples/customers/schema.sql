CREATE TABLE customers (
    customer_id serial PRIMARY KEY,
    full_name   text NOT NULL,
    email       text NOT NULL UNIQUE,
    city        text NOT NULL
);

CREATE TABLE orders (
    order_id           serial PRIMARY KEY,
    customer_id        integer NOT NULL REFERENCES customers (customer_id),
    status             text NOT NULL
                       CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled')),
    total_amount       numeric(10, 2) NOT NULL CHECK (total_amount >= 0),
    created_at         timestamptz NOT NULL DEFAULT now(),
    estimated_delivery date
);
