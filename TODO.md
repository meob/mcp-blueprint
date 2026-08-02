# TODO

This document contains the implementation backlog for **MCP Blueprint**.

Tasks are intentionally small and independent so they can be implemented by AI coding assistants with minimal context switching.

Checkboxes track the current MVP status.

---

# MVP

## Project bootstrap

* [x] Create Python project structure
* [x] Configure pyproject.toml
* [x] Configure Ruff
* [x] Configure Black
* [x] Configure pytest
* [x] Configure mypy
* [x] Configure pre-commit hooks

---

## Core framework

* [x] Create Blueprint application class
* [x] Implement configuration loader
* [x] Implement YAML parser
* [x] Implement SQL loader
* [x] Implement Jinja2 rendering
* [x] Implement parameter validation
* [x] Implement error handling
* [x] Implement structured logging

---

## FastMCP integration

* [x] Initialize FastMCP server
* [x] Automatic tool registration
* [x] Parameter conversion
* [x] Tool documentation generation
* [x] Error propagation
* [x] JSON response formatting

---

## Transport

### stdio

* [x] Implement stdio transport
* [ ] Test with Claude Desktop
* [ ] Test with OpenCode
* [ ] Test with Gemini CLI

### Streamable HTTP

* [x] Implement Streamable HTTP transport
* [x] Configuration options
* [ ] Health endpoint
* [ ] Docker example

---

# Database Layer

## Generic adapter

* [x] Define DatabaseAdapter interface
* [x] Connection abstraction
* [x] Query execution
* [ ] Transaction management
* [x] Connection pooling

---

## PostgreSQL adapter

* [x] psycopg3 implementation
* [x] Async support
* [x] Connection pool
* [x] Connection testing

---

## Oracle adapter

* [ ] Oracle implementation

---

## ClickHouse adapter

* [ ] ClickHouse implementation

---

## MySQL adapter

* [ ] MySQL implementation

---

# Tool System

* [x] YAML tool loader
* [x] Automatic validation
* [x] Parameter parsing
* [x] SQL execution
* [x] Result serialization

---

# SQL Templates

* [x] Jinja2 integration
* [x] Conditional SQL
* [x] Optional parameters
* [x] SQL syntax validation

---

# Formatting

* [x] Column rename support
* [x] Unit conversion
* [x] Timestamp formatting
* [ ] Duration formatting
* [ ] Computed columns
* [x] Hidden columns

---

# Cache

* [x] Cache abstraction
* [x] cachetools backend
* [ ] aiocache backend
* [x] Per-tool TTL
* [ ] Cache invalidation

---

# Security

* [x] Tool enable/disable
* [x] Role metadata
* [x] Confirmation flag
* [ ] Future authentication hooks

---

# Configuration

* [x] server.yaml
* [x] database.yaml
* [x] logging.yaml
* [x] pack.yaml

---

# PostgreSQL DBA Pack

The PostgreSQL DBA Pack is the reference implementation for the framework.

## Sessions

* [x] get_connections()
* [x] get_active_sessions()
* [ ] get_idle_sessions()
* [x] get_long_running_queries()

---

## Locks

* [x] get_blocking_sessions()
* [ ] get_lock_tree()
* [x] get_wait_events()

---

## Storage

* [x] get_database_size()
* [ ] get_tablespace_size()
* [ ] get_table_size()
* [ ] get_index_size()

---

## Maintenance

* [ ] get_autovacuum_status()
* [ ] get_vacuum_progress()
* [ ] get_analyze_status()

---

## Bloat

* [ ] get_table_bloat()
* [ ] get_index_bloat()

---

## Transactions

* [ ] get_xid_status()
* [ ] get_oldest_transactions()

---

## Performance

* [ ] get_top_queries()
* [ ] get_expensive_queries()
* [ ] get_io_statistics()

---

## Replication

* [x] get_replication_status()
* [ ] get_replication_lag()
* [ ] get_wal_statistics()

---

# Oracle DBA Pack

* [ ] Initial implementation

---

# SQL Server DBA Pack

* [ ] Initial implementation

---

# MySQL DBA Pack

* [ ] Initial implementation

---

# Documentation

* [x] Installation guide
* [x] Quick start
* [x] Pack development guide
* [ ] Adapter development guide
* [ ] Contribution guide

---

# Examples

* [x] PostgreSQL example
* [ ] Oracle example
* [ ] Customer Pack example
* [ ] ERP Pack example

---

# Testing

* [x] Unit tests
* [x] Integration tests
* [ ] PostgreSQL CI
* [ ] Oracle CI
* [ ] SQL Server CI
* [ ] MySQL CI

---

# Docker

* [ ] Dockerfile
* [ ] Docker Compose example
* [ ] Streamable HTTP example

---

# Future Features

## Workflow Tools

Higher-level tools orchestrating multiple atomic tools.

Examples:

* [ ] diagnose_performance()
* [ ] diagnose_storage()
* [ ] diagnose_autovacuum()
* [ ] diagnose_replication()

---

## AI-assisted Features

* [ ] Tool self-documentation
* [ ] Automatic OpenAPI-like documentation
* [ ] Tool usage statistics
* [ ] Performance metrics

---

## Nice to Have

* [ ] Plugin system
* [ ] Pack installer
* [ ] Pack repository
* [ ] Web administration UI
* [ ] Metrics endpoint
* [ ] Prometheus integration
* [ ] NoSQL adapters

---

# Long-term Vision

The objective is not simply to create another MCP server.

The objective is to establish a reusable architecture for building domain-oriented MCP servers.

Developers should spend their time defining **tools**, **SQL**, and **business concepts**, while the framework handles infrastructure, transport, validation, caching, formatting, and database abstraction.

Ultimately, adding a new tool should require little more than creating:

* one YAML definition
* one SQL file

without writing additional Python code.
