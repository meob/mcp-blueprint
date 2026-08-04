# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-08-04

### Fixed

- DBA packs report sizes as raw byte counts in a single `size_bytes` column
  across all engines; the engine-specific human-readable `size`/`size_mb`
  strings (`pg_size_pretty()`, `FORMAT()`, `ROUND(...) || ' MB'`,
  `formatReadableSize()`) were removed (decision D14).
- CI pipeline: bumped `actions/checkout@v5` and `astral-sh/setup-uv@v7`
  (Node 24, removing the Node.js 20 deprecation warning), ran the unit-test
  command from a proper `run` block so the folded backslash is not parsed as
  an argument, and created the log directory before attaching file handlers so
  integration jobs no longer fail on a fresh checkout.
- `get_connections` test no longer asserts that a client session exists,
  which was environment-dependent (a fresh database reports only background
  processes and the monitoring session is deliberately excluded).

## [0.2.0] - 2026-08-04

### Added

- Oracle, ClickHouse, SQL Server and MariaDB DBA packs, completing the six
  reference engines behind the `DatabaseAdapter` interface.
- Docker compose demo with least-privilege monitoring roles and
  `pg_stat_statements`.
- Custom pack tutorial, best practices, FAQ and a customers example pack.

[Unreleased]: https://github.com/meob/mcp-blueprint/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/meob/mcp-blueprint/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/meob/mcp-blueprint/compare/v0.2.0
