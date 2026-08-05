# Best practices

How to author packs that get good results from LLM agents.  The tool metadata
you write is the *only* interface the agent sees, so its quality determines
the quality of the answers.

## Write for the agent, in English

Every agent-facing text — tool descriptions, parameter descriptions, pack
`instructions` — must be **in English**, even when the agent can converse in
other languages.  Agents perform better on precise, consistent English, and
the same tool descriptions are consumed by many clients.

Be **precise but concise**: 1–3 sentences per description.  State what the
agent learns, the accepted parameter values, and the edge cases ("returns no
rows when the customer does not exist").  Long prose dilutes the signal; so
does vague wording.

## Expose concepts, not SQL

Name tools after questions the domain asks, not after statements:

* `get_connections` — not `execute_sql`
* `search_customers` — not `query_customers_table`

If a prompt has to mention SQL to get an answer, the pack is wrong.

## Keep the tool count small

A tool should be something the agent *frequently* needs.  Typical sizes:

| Kind        | Tools | Example               |
| ----------- | ----- | --------------------- |
| Domain pack | 4–8   | `examples/customers`  |
| DBA pack    | ~13   | `packs/pg-dba`        |

If two tools differ only by a value, merge them with an optional parameter
instead of duplicating.

## Naming

* Lowercase `snake_case`, matching `^[a-z][a-z0-9_]*$`.
* Verb first: `get_`, `search_`, `list_`, `count_`.
* Use the same verb for the same intent across packs: `get_*` always returns
  one record, `search_*` always returns a list.

## Descriptions

* Tell the agent what it learns by calling the tool.
* Document the accepted parameter values ("one of pending, shipped,
  delivered, cancelled").
* State the edge cases: empty results, missing records, overdue semantics.
* Keep parameter `description`s short but unambiguous.

## Pack instructions

`pack.yaml → instructions` is appended to *every* tool description and to the
server instructions.  Use it for:

* the recommended call order ("first `search_customer`, then
  `customer_account_summary`");
* domain rules the tools cannot express ("check what the customer still has
  on loan before recommending new films", "prefer categories the customer
  already rents");
* what to do on failure ("if the search returns no match, say so instead of
  inventing an account").

## Parameters and filters

* Optional filters with Jinja `{% if %}` instead of near-identical tools.
* Values reach the SQL only as bound placeholders (`%(name)s`).
* Wrap wildcards in the SQL, never ask the agent for them:
  `ILIKE '%%' || %(title)s || '%%'`.

## Result shape

* Deterministic `ORDER BY` on every query.
* `LIMIT` on every query; the server additionally caps results at
  `server.max_rows`.
* One statement per query — the framework rejects stacked statements.

## KPI convention

Diagnostic dashboards return one row per KPI with columns
`kpi_name, current_value, unit, suggested_threshold, status`, where `status`
is `ok`, `warning` or `error`.  Never filter rows out by severity: the agent
must always see the whole dashboard.  KPIs without a meaningful threshold use
`suggested_threshold: n/a` and `status: ok`.

## Security

* Tools are read-only by default; the guard is fail-closed and enforced at
  load time and at runtime.
* Opt in to writes explicitly with `writes: true`; keep it the exception.
* No `{{ expr }}` interpolation in templates (rejected at load time) and no
  SQL embedded in Python code.

## Keep packs decoupled from the framework

Packs are configuration, so keep them in your own repository and install
mcp-blueprint as a dependency.  This makes upgrades a dependency bump instead
of a merge.  See the [tutorial](tutorial.md) section on updating.
