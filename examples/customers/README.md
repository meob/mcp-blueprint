# Customers example pack

A minimal Customer/CRM pack used by the [tutorial](../docs/tutorial.md).  It
shows the recommended shape of a single-engine domain pack: four
concepts-as-tools, optional filters, a KPI dashboard and a real
`instructions` block.

## Tools

| Tool                  | Purpose                                     |
| --------------------- | ------------------------------------------- |
| `search_customers`    | Find customers by name or city.             |
| `get_customer`        | Full customer record with an order summary. |
| `get_customer_orders` | List a single customer's orders.            |
| `get_orders_kpis`     | Order health KPIs across all customers.     |

## Using it

Copy the directory into `packs/` and load it on a PostgreSQL engine, or point
`server.packs_dir` at the parent directory and use the pack allowlist.  See
`docs/tutorial.md` for the full walkthrough.

Provision a demo database:

```sh
psql "$DATABASE_URL" -f examples/customers/schema.sql
psql "$DATABASE_URL" -f examples/customers/seed.sql
```
