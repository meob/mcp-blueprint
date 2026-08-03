# syntax=docker/dockerfile:1

# ---------- Builder stage ----------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Some wheels (e.g. asyncmy) are not published for every architecture and
# must be compiled from source.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install the runtime dependencies first so the layer is cached independently
# of the source code.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN uv sync --frozen --no-dev --no-install-project

# Install the project itself (blueprint package and its entry point) as a
# regular wheel so the runtime image does not need the source tree.
COPY blueprint ./blueprint
RUN uv sync --frozen --no-dev --no-editable

# ---------- Runtime stage ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/.venv ./.venv

# Configuration, packs and the template skeleton shipped inside the image.
COPY config ./config
COPY packs ./packs
COPY template ./template

# Writable directory for the rotating log and audit files.
RUN mkdir -p /app/logs

# Run as an unprivileged user.
RUN useradd --create-home --uid 1000 app
RUN chown -R app:app /app
USER app

EXPOSE 8000

CMD ["blueprint", "serve", "--config", "config", "--transport", "http"]
