# ADR 0002: Django Foundation and Local Tooling

- Status: Accepted
- Date: 2026-07-16

## Context

ADR 0001 selected Django and PostgreSQL but deferred the application layout, exact runtime series, dependency management, settings structure, local database workflow, and Python quality tools.

The repository is a cloud-platform monorepo. Its Django backend needs a clear boundary from future infrastructure and delivery code. The custom user model also needs to exist before the first database schema is established because changing `AUTH_USER_MODEL` later is disruptive.

## Decision

Place the Django backend under `app/`. Use `app/config/` for Django project configuration and `app/apps/` for domain applications. Import the initial users application as `apps.users`, retain the Django app label `users`, and configure `AUTH_USER_MODEL = "users.User"`.

Use:

- Python 3.13, constrained to `>=3.13,<3.14`;
- Django 5.2 LTS;
- uv with an application-style `pyproject.toml`, `app/.venv`, and committed `uv.lock`;
- one environment-driven `config/settings.py`;
- django-environ for typed settings and local `.env` loading;
- PostgreSQL as the only normal application database;
- Psycopg 3 with its binary implementation for local development;
- PostgreSQL 17 as a health-checked Docker Compose service with a named volume;
- pytest and pytest-django;
- Ruff for formatting and linting.

The direct versions resolved during TASK-001 are:

| Dependency | Resolved version |
| --- | --- |
| Django | 5.2.16 |
| django-environ | 0.14.0 |
| psycopg | 3.3.4 |
| psycopg-binary | 3.3.4 |
| pytest | 9.1.1 |
| pytest-django | 4.12.0 |
| Ruff | 0.15.22 |

The validated local tool/runtime versions are:

| Tool/runtime | Validated version |
| --- | --- |
| uv | 0.11.29 |
| Python | 3.13.14 |
| PostgreSQL | 17.10 |

Compatible minor-series constraints remain in `pyproject.toml`; `uv.lock` is the exact reproducible resolution for direct and transitive dependencies.

## Rationale

Python 3.13 is explicitly selected because the development machine also has Python 3.14 and the project must not depend on ambiguous system resolution. Django 5.2 provides an LTS support window suitable for a production-oriented portfolio.

The `app/` boundary keeps application concerns distinct from future infrastructure and delivery code. The `config/` and `apps/` split makes project settings distinguishable from domain behavior without introducing empty future directories.

The minimal `AbstractUser` subclass makes the user model swappable from the initial migration without prematurely adding authentication requirements. PostgreSQL through Compose gives Windows development a repeatable database while Django continues to run directly through uv.

django-environ provides typed environment parsing and allows real process variables to take precedence over an ignored local `.env`. pytest and Ruff provide a compact test and quality toolchain that can later run unchanged in CI.

## Alternatives considered

- Python 3.14 was rejected for this task in favor of the explicitly approved 3.13 runtime.
- Django 6.0 was rejected because this foundation benefits more from Django 5.2's longer LTS window than from newer framework features.
- Split settings modules were deferred because no production settings behavior exists yet.
- Django's built-in `User` was rejected because replacing it after initial migrations would be unnecessarily difficult.
- PostgreSQL 18 was considered, but PostgreSQL 17 offers a mature supported baseline for later RDS work.
- Black, isort, and Flake8 were considered, but Ruff provides the needed formatting and linting with less configuration.
- Cookiecutter Django and other third-party foundations were rejected because their unrelated features conflict with the project's incremental scope and history goals.

## Consequences

Application commands must run from `app/`, and future CI jobs and editor configuration must use that working directory. Future domain applications will use import paths such as `apps.projects` and `apps.tasks`.

Local developers need uv and Docker Desktop. Values used by Compose and `DATABASE_URL` must remain consistent. The `postgres:17` major tag receives supported minor updates when pulled; production image and database version policies will be decided in later tasks.

The initial custom user has no additional fields or behavior. Public registration, JWT, email authentication, profiles, and API endpoints remain deferred.
