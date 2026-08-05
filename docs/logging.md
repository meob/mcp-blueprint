# Logging, audit and tracing

MCP Blueprint owns the operational side of observability: structured logging,
an audit trail and request correlation.  Nothing is persisted by default —
the framework only writes a JSON stream to `stderr` — and every extra channel
is enabled through `config/logging.yaml`.

## Default behaviour

* Logs are structured JSON written to `stderr` (under the stdio transport
  `stdout` is reserved for the MCP protocol stream).
* No file is written, no audit trail is produced.

## Main log

```yaml
logging:
  level: info        # debug | info | warning | error
  format: json       # json | console
```

To persist the main log to a rotating file:

```yaml
logging:
  level: info
  format: json
  file_path: logs/blueprint.jsonl   # default: stderr only
  file_max_bytes: 10485760          # 10 MiB per file
  file_backups: 5
```

The file uses the same structured JSON lines as `stderr`, with rotation based
on size (`RotatingFileHandler`).

## Audit log

The audit channel records **one JSON line per tool execution**, both on
success and on failure:

```yaml
logging:
  audit:
    enabled: true
    file_path: logs/audit.jsonl
    max_bytes: 10485760
    backups: 5
```

Record schema (success):

```json
{
  "tool": "recommend_films",
  "pack": "sakila",
  "params": {"category": "Family"},
  "duration_ms": 44.66,
  "rows": 2,
  "status": "success",
  "cache_hit": false,
  "event": "tool_executed",
  "trace_id": "161d3c9c7f154cfb8312eddd9d3cb9f9",
  "level": "info",
  "timestamp": "2026-08-03T11:56:52.618243Z"
}
```

On failure the event is `tool_failed`, `status` is `error` and an `error`
field carries the message.  The audit logger is `audit`; it never propagates
to the main log and is fully inert while disabled.

Calls rejected by parameter validation are recorded too: the framework
validates arguments before the MCP layer, so a `tool_failed` record is written
for every rejected call with `status: "error"` and the validation message.

## Request correlation (tracing)

Every tool call binds a `trace_id` (a random hex string) before execution and
releases it afterwards.  The identifier is merged into **all** log and audit
records produced during the call, so events from a single request can be
correlated by grep on `trace_id`.  This is the lightweight foundation for
OpenTelemetry, which may be added later as an optional extra.

## Sensitive data redaction

A redaction processor runs on every event before rendering.  Values whose
keys contain any of `password`, `passwd`, `pwd`, `secret`, `token`,
`api_key`, `authorization`, `credential`, `private_key`, `access_key`, `dsn`,
`connstring` or `connection_string` are replaced with `***` — recursively,
including tool parameters and lists.  The behaviour is enabled by default and
cannot be turned off; connection strings are never logged in full.
