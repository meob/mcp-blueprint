# Prometheus metrics

MCP Blueprint exposes an optional Prometheus endpoint with the full framework
metric catalog (tools, cache, database, pool and server).  It is disabled by
default and requires the optional `metrics` extra.

## Activation

```bash
uv sync --all-extras --dev        # or: pip install "mcp-blueprint[metrics]"
```

Enable the endpoint in `config/metrics.yaml`:

```yaml
metrics:
  enabled: true
  host: 127.0.0.1
  port: 9100
```

The endpoint is served on `host:port/metrics` from a background thread and is
independent of the MCP transport, so **stdio servers are scrapeable too**.  On
startup the server prints the endpoint address to `stderr`:

```
serving Prometheus metrics at http://127.0.0.1:9100/metrics
```

Nothing is exposed when `metrics.enabled` is false.  The framework never pays
for the dependency in that case: `prometheus-client` is imported lazily and a
clear configuration error is raised at startup if metrics are enabled without
the extra installed.

## Metric catalog

All metrics are namespaced with `blueprint_`.  Labels are bounded — `tool`,
`pack`, `status`, `engine` — never per-request values.

### Tools

| Metric | Type | Labels | Meaning |
| ------ | ---- | ------ | ------- |
| `blueprint_tool_calls_total` | counter | `tool`, `pack`, `status` | Invocations by status (`success`/`error`), including validation rejections |
| `blueprint_tool_duration_seconds` | histogram | `tool`, `pack` | Execution latency in seconds |
| `blueprint_tool_rows` | histogram | `tool` | Rows returned per call |

### Cache

| Metric | Type | Labels | Meaning |
| ------ | ---- | ------ | ------- |
| `blueprint_tool_cache_hits_total` | counter | `tool` | Cache hits |
| `blueprint_tool_cache_misses_total` | counter | `tool` | Cache misses |
| `blueprint_cache_entries` | gauge | — | Current number of cached entries |
| `blueprint_cache_maxsize` | gauge | — | Configured cache max size |

### Database

| Metric | Type | Labels | Meaning |
| ------ | ---- | ------ | ------- |
| `blueprint_db_queries_total` | counter | `engine` | Queries executed |
| `blueprint_db_query_duration_seconds` | histogram | `engine` | Query latency in seconds |
| `blueprint_db_errors_total` | counter | `engine` | Queries that failed |

### Pool

| Metric | Type | Labels | Meaning |
| ------ | ---- | ------ | ------- |
| `blueprint_db_pool_size` | gauge | `engine` | Current open connections |
| `blueprint_db_pool_idle` | gauge | `engine` | Current idle connections |
| `blueprint_db_pool_max` | gauge | `engine` | Maximum pool size |
| `blueprint_db_pool_waiting` | gauge | `engine` | Queries waiting for a connection |

### Server

| Metric | Type | Labels | Meaning |
| ------ | ---- | ------ | ------- |
| `blueprint_tools_registered` | gauge | — | Number of registered tools |
| `blueprint_packs_loaded` | gauge | — | Number of loaded packs |

The default registry also serves the standard `process_*` and `python_info`
metrics.

## Scraping

Add the endpoint to Prometheus:

```yaml
scrape_configs:
  - job_name: mcp-blueprint
    static_configs:
      - targets: ["127.0.0.1:9100"]
```

## Design notes

* Instrumentation is optional end to end: each component receives a `Metrics`
  instance only when enabled and silently does nothing otherwise.
* Counter/histogram/gauge definitions live in `blueprint/metrics.py`; cache,
  pipeline, validation gate, adapters and pack loader only call small helpers.
* The endpoint is safe for stdio: it never writes to `stdout`.
