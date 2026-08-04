# FAQ

## How many tools should my pack expose?

Enough for the agent to answer the questions of your domain, not more.
4–8 tools for a domain pack, around 13 for a DBA-style pack.  Merge tools
that differ only by a value into one tool with optional parameters.

## What naming conventions should I use?

Lowercase `snake_case` (`^[a-z][a-z0-9_]*$`), verb first: `get_`, `search_`,
`list_`, `count_`.  Use the same verb for the same intent everywhere.

## How should I write tool descriptions?

In English, precise but concise (1–3 sentences): what the agent learns, the
accepted parameter values and the edge cases.  See
[docs/best_practices.md](best_practices.md).

## Do I need to remove the reference packs?

No.  Use the allowlist `MCP_BLUEPRINT_SERVER_PACKS=my-pack` in `server.yaml`
to load only your packs, or point `server.packs_dir` at your own directory.
Reference packs are only loaded when they match the configured engine and the
allowlist.

## Where do I start?

Clone the repository (`git clone https://github.com/meob/mcp-blueprint.git`),
run `uv sync --all-extras --dev`, copy `template/pack` into `packs/` and
follow [the tutorial](tutorial.md).  A complete worked example ships in
[`examples/customers`](../examples/customers).

## Do I need to write Python?

No.  A pack is YAML + SQL.  Python is only needed if you write a new database
adapter (see `blueprint/db/base.py`).

## How do I keep my packs up to date as mcp-blueprint evolves?

Keep your packs in your own repository and use mcp-blueprint as a dependency
(see `server.packs_dir`).  Upgrades become a dependency bump; the pack
contract is stable and additive, and load-time validation fails loudly if
anything ever breaks.  New engines are opt-in via `engines:` in `pack.yaml`.

## My tool needs to modify data.  How?

Set `writes: true` in the tool metadata.  Everything else stays read-only,
and the SQL must remain a single statement.

## Can one tool work on several engines?

Yes.  Declare `sql` as a map keyed by engine and give each engine its own SQL
file, or share one file and restrict it with `engines:`.

## Where is the full reference?

[docs/pack_development.md](pack_development.md) describes the whole pack
format.  [docs/best_practices.md](best_practices.md) has the authoring
checklist, and [docs/tutorial.md](tutorial.md) walks you through building a
server end to end.
