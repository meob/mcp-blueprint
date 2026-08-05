# Sakila pack

`packs/sakila` is the canonical domain-oriented pack for the [Sakila sample
database](https://dev.mysql.com/doc/sakila/en/) on PostgreSQL.  It lets an
agent run a DVD rental store chatbot — recommend films, inspect stock,
review a customer's account — without ever writing SQL.

The pack declares `engines: [postgresql]` and is loaded only when
`database.engine` is `postgresql`.

## Design principle: verticalized tools

The tools are *verticalized*: business logic lives server-side, inside the
pack, instead of being left to the model.  Tools accept names and titles
directly — `customer_account_summary("tammy sanders")`, not a lookup that
returns an id which the agent then must chain into a second call — and return
a complete business answer (account standing, on-loan films with overdue
markers, recommendations that exclude what the customer has already rented).

This is what a benchmark of the framework measures: on the same database and
task set, a pack of thin, table-shaped lookups scored barely better than
generic SQL, while these verticalized tools reached 0.996 mean accuracy
versus 0.711 for SQL at a fraction of the tokens and latency.  The lesson for
pack authors: an example pack must demonstrate the value proposition —
encapsulate the domain so the agent decides *what* is needed, not *how*.

## Tools

| Tool                     | Purpose                                              |
| ------------------------ | ---------------------------------------------------- |
| `search_customer`        | Find a customer by first/last/full name.             |
| `customer_account_summary` | Full account snapshot: standing, on-loan, overdue. |
| `rental_history`         | What a customer has rented in the past.              |
| `recommend_films`        | Popular film suggestions, new to a given customer.   |
| `film_stock`             | Per-store availability for a film by title.          |

### `search_customer(name)`

Finds customers by first name, last name or full name (case-insensitive
substring), returning `customer_id`, contact details and store.  This is the
identification step: it confirms the customer exists before the account tools
run, and every other tool re-resolves the name itself so the agent does not
have to carry an id around.

### `customer_account_summary(customer_name)`

One row per matching customer with contact info, home `store_id`, rental
counts (`total_rentals`, `open_rentals`, `overdue_rentals`), an explicit
`standing` flag and the films currently on loan:

* `standing` is `GOOD STANDING` when nothing is overdue, `HAS OVERDUE`
  otherwise.
* `open_films` is a comma-separated list of on-loan titles with `(OVERDUE)`
  appended to past-due items, or `NONE` when nothing is on loan.

This is the tool to call when a customer asks about their account, their
standing, or "what do I still have to return".

### `rental_history(customer_name)`

The most recent 25 rentals with the rental date and a computed `status`:

* `returned` — already returned (history)
* `active` — rented out, not yet due
* `overdue` — rented out past the rental duration

### `recommend_films(customer_name?, category?, rating?, count=3, in_stock_only=true)`

Popular films ordered by number of rentals, each with `rating`, `length` and
`available_copies`.  When `customer_name` is given, films that customer has
already rented are excluded, so suggestions are always new.  The category
parameter understands common synonyms (`Science Fiction` for `Sci-Fi`) and
even tolerates a rating code being passed as the category; `in_stock_only`
(default true) filters to films with at least one copy available.  Used both
for per-customer recommendations and generic "what should I watch?" requests
(omit `customer_name`).

### `film_stock(title, store_id?)`

Per-store stock for a film found by title substring, returning one row per
store with `total_copies`, `available` (copies not on loan), `rating` and
`length`.  Pass `store_id` to restrict to a single store.

## Guiding the agent

Tool descriptions are the interface between the pack and the agent.  Each
description states *when* to call the tool and which tools overlap: the
account tools say "use `rental_history` for the past", the history tool says
"use `customer_account_summary` for what is on loan right now".  The pack
also carries `instructions` (see `pack.yaml`) with the recommended workflow.
No Python code is needed to teach the agent this behaviour.

## Domain logic lives in SQL

Entity resolution (name → customer), business rules (standing, overdue,
on-loan) and product logic (popularity ordering, excluding already-seen
films) are all encoded in the pack's `sql/` queries.  Writing the domain in
SQL keeps the framework generic and lets the person who knows the database
encode it once, in the place every model will reuse.

## Tests

`tests/test_pack_sakila.py` runs the five tools against a live Sakila
database and is skipped when it is not reachable.  Point the tests at a
different instance with:

```sh
MCP_BLUEPRINT_SAKILA_URL=postgresql://user:pass@host:5432/sakila \
  uv run pytest tests/test_pack_sakila.py
```
