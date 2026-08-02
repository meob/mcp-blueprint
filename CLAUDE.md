# CLAUDE.md

This document defines the general development guidelines for AI coding assistants contributing to this repository.

These guidelines are intentionally project-independent and should remain applicable across different projects.

Project-specific requirements are documented in the repository documentation.

---

# General Principles

Produce software that is:

* Correct
* Readable
* Maintainable
* Modular
* Production-ready

Always prefer simplicity over unnecessary complexity.

Choose solutions that minimize long-term maintenance.

---

# Read the Documentation First

Before making significant changes, read the Markdown documentation available in the project root.

The project documentation defines:

* goals
* architecture
* implementation priorities
* design decisions

Follow the documented architecture unless explicitly instructed otherwise.

---

# Language

Use English consistently for:

* source code
* comments
* docstrings
* documentation
* commit messages
* prompts
* examples
* configuration descriptions
* error messages

Do not mix languages.

---

# Code Quality

Write clean, explicit and readable code.

Prefer:

* small functions
* focused classes
* modular components
* reusable code

Avoid:

* duplicated logic
* unnecessary abstractions
* premature optimization
* hidden side effects

Prefer composition over inheritance whenever practical.

---

# Dependencies

Keep dependencies to a minimum.

Before introducing a new library, verify that it provides significant value.

Avoid overlapping libraries that solve the same problem.

---

# Configuration

Avoid hardcoded values.

Use configuration files or environment variables whenever appropriate.

---

# Testing

Whenever practical, accompany new functionality with automated tests.

Code without tests should be considered incomplete.

---

# Documentation

Documentation is part of the implementation.

Whenever functionality or architecture changes, update the relevant documentation.

---

# Git

Use Git from the beginning.

Create small, coherent commits.

Write concise and descriptive commit messages.

---

# Open Source Mindset

Assume the repository may become public.

Never include:

* credentials
* passwords
* tokens
* private URLs
* confidential information
* company-specific details unless explicitly required

---

# Repository Organization

Keep the repository clean and organized.

The `/staff` directory is reserved for personal notes, experiments, temporary scripts and other non-production material.

Rules:

* never import code from `/staff`
* never reference `/staff` from production code
* assume `/staff` is ignored by Git
* do not include `/staff` in project documentation

---

# Architecture

Respect the documented architecture.

Avoid shortcuts that bypass the intended design.

If a better architectural solution is identified, update the documentation before implementing major structural changes.

---

# AI Collaboration

Act as a long-term contributor rather than a one-time code generator.

Before implementing changes:

1. Understand the existing code.
2. Read the project documentation.
3. Preserve architectural consistency.
4. Prefer incremental improvements over large rewrites.

When requirements are unclear, ask for clarification instead of making major assumptions.
