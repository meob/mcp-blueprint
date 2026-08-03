# Sakila pack

`packs/sakila` is a domain-oriented pack for the [Sakila sample
database](https://dev.mysql.com/doc/sakila/en/) on PostgreSQL.  It lets an
agent run a DVD rental store chatbot: recommend films, inspect a film in
detail and review a customer's rental activity — without ever writing SQL.

The pack declares `engines: [postgresql]` and is loaded only when
`database.engine` is `postgresql`.

## Tools

| Tool                   | Purpose                                            |
| ---------------------- | -------------------------------------------------- |
| `search_films`         | Recommend films by optional title, category, rating. |
| `get_film`             | Full catalog record for one film.                  |
| `search_customer`      | Find a customer by first or last name.             |
| `get_customer_rentals` | Rental history with an active/overdue/returned status. |

### `search_films(title?, category?, rating?)`

Returns films ordered by popularity (number of rentals), so the "best" films
surface first.  Each row includes the MPAA `rating` code, a human-readable
`rating_label`, a numeric `min_age`, `length`, `rental_rate`, `popularity`
and `available_copies`.

The rating code is translated in SQL, not in Python: the pack author encodes
domain knowledge once in the query, e.g. `PG-13 - under 17 requires
accompanying parent or guardian` with `min_age = 13`.

### `get_film(film_id)`

Returns a single row with the film description, translated rating,
`rental_rate`, `rental_duration`, `replacement_cost`, `special_features`, the
full cast as a comma-separated list, its categories and per-store
availability (e.g. `Store 1: 4 available, Store 2: 3 available`).

### `search_customer(name)`

Finds customers by a first or last name substring (case-insensitive),
returning the customer id, contact details and store.

### `get_customer_rentals(customer_id)`

Returns the customer's rentals newest first with the film title, dates and a
computed `status`:

* `active` — rented out, not yet due
* `overdue` — rented out past the rental duration
* `returned` — already returned (history)

One result set covers both "DVDs to return" and "what the customer has seen".
This is the tool to call when a customer asks about their situation: the
`search_customer` description points the agent to it with the resulting
`customer_id`.

## Guiding the agent

Tool descriptions are the interface between the pack and the agent.  Keep
them concrete about *when* to call a tool: `search_customer` explains that it
is the first step when a customer asks about their account, and
`get_customer_rentals` explains it answers "what do I still have to return".
No Python code is needed to teach the agent this workflow.

## Domain translations live in SQL

Code values are made comprehensible for the agent inside the queries (the
`rating_label`/`min_age` CASE above, and the computed rental `status`).
Writing the translation in SQL keeps the framework generic and lets the
person who knows the database encode the domain.

## Tests

`tests/test_pack_sakila.py` runs the four tools against a live Sakila
database and is skipped when it is not reachable.  Point the tests at a
different instance with:

```sh
MCP_BLUEPRINT_SAKILA_URL=postgresql://user:pass@host:5432/sakila \
  uv run pytest tests/test_pack_sakila.py
```
