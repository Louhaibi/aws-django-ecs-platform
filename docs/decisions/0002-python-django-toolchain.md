# ADR 0002: Python and Django Toolchain

## Status

Accepted

## Context

The application requires a consistent and reproducible toolchain across development, continuous integration, and containers. Dependencies, formatting, testing, and database behavior must remain predictable as the application evolves.

## Decision

Python 3.13 is the supported language series. CI and container definitions use exact Python patch pins where reproducibility is required.

The application uses Django 5.2, Django REST Framework, uv for dependency resolution and locked installation, pytest with pytest-django for testing, Ruff for formatting and linting, and PostgreSQL as the supported database.

These choices prioritize compatibility, maintained release lines, dependency locking, consistency across environments, and predictable CI and container builds.

## Consequences

Toolchain upgrades require coordinated changes to the lockfile, CI configuration, and container definitions. Exact pins improve reproducibility but require deliberate maintenance when newer releases are adopted.

PostgreSQL-backed tests represent supported runtime behavior more accurately than an alternate database. A focused toolchain reduces configuration duplication across development, testing, continuous integration, and container builds.

## Alternatives considered

Pip with requirements files is widely used but provides less integrated dependency resolution and lockfile workflow than uv.

Poetry provides dependency management and packaging features but is not required for the current application workflow.

SQLite for tests would reduce setup cost but would not exercise the supported PostgreSQL behavior.

Separate formatting and linting tools can provide equivalent coverage but would add configuration and execution steps that Ruff consolidates.
