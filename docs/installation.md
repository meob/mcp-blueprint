# Installation

## Requirements

* Python 3.12 or newer
* A PostgreSQL instance (only needed for the PostgreSQL DBA pack)

## Install from source

```bash
git clone <repository-url>
cd mcp-blueprint
uv sync --all-extras --dev
```

This creates a virtual environment in `.venv` and installs all runtime and
development dependencies.

The `blueprint` command line tool is available through the virtual
environment:

```bash
uv run blueprint --help
```

## Install as a package

```bash
pip install -e .
# or
uv pip install -e .
```

After installation the `blueprint` executable is on your `PATH`.

## Development tools

The repository ships with:

| Tool       | Purpose             | Command                      |
| ---------- | ------------------- | ---------------------------- |
| Ruff       | Linting + formatting | `uv run ruff check .`       |
| mypy       | Static typing        | `uv run mypy blueprint`     |
| pytest     | Tests                | `uv run pytest`             |
| pre-commit | Git hooks            | `pre-commit install`        |

Run all checks with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy blueprint
uv run pytest
```
