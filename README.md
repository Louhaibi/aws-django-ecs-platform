# AWS Django ECS Platform

A containerized Django REST API for project and task management, backed by
PostgreSQL and prepared for deployment on AWS ECS.

## Overview

The application provides authenticated project and task management through a documented REST API and Django Admin. It runs locally with Docker Compose, uses PostgreSQL for persistence, and includes automated validation for application quality and container builds.

## Features

- user authentication with JSON Web Tokens (JWT);
- projects, project membership, tasks, assignment, status, priority, and due dates;
- object-level authorization and validation;
- Django Admin for administrative management;
- OpenAPI schema and Swagger UI;
- PostgreSQL-backed automated tests;
- database-aware health endpoint at `/health/`;
- multi-stage, non-root Gunicorn container image;
- Docker Compose services for PostgreSQL, migrations, and the web application;
- GitHub Actions checks for application validation and container builds.

## Architecture

The Django application uses Django REST Framework for HTTP APIs, Django Admin for administrative operations, and PostgreSQL as its supported database. Configuration is environment-based.

Docker Compose runs three services locally:

- `db` provides PostgreSQL 17 with persistent storage;
- `migrate` applies database migrations and must complete before the web service starts;
- `web` runs Gunicorn as a non-root user and exposes the API.

The container image uses a multi-stage build with locked dependencies. The current design is compatible with a future AWS ECS runtime, but AWS infrastructure and deployment are not implemented.

## Repository structure

```text
.
|-- .github/
|   `-- workflows/ci.yml     # Continuous integration workflow
|-- app/
|   |-- apps/                # Django domain applications
|   |-- config/              # Django configuration and health endpoint
|   |-- tests/               # Automated tests
|   |-- Dockerfile           # Multi-stage non-root application image
|   |-- compose.yaml         # Local PostgreSQL, migration, and web services
|   |-- pyproject.toml       # Dependencies and tool configuration
|   `-- uv.lock              # Locked dependency resolution
|-- docs/
|   `-- decisions/           # Architecture decisions
|-- CONTRIBUTING.md
`-- README.md
```

## Prerequisites

- Docker Desktop running Linux containers with Docker Compose v2;
- Python 3.13 and uv for host-based commands;
- Git.

Docker Desktop must be running before Compose commands. Host access uses `127.0.0.1`; `db` and `web` are Compose-network hostnames rather than host URLs.

## Quick start

From `app/`:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
docker compose ps --all
```

Keep `.env` out of version control and use only development values. `JWT_SIGNING_KEY` is required and is separate from `DJANGO_SECRET_KEY`. Keep the `POSTGRES_*` values consistent; Compose constructs its internal database connection with hostname `db`.

Expected services:

- `db` is healthy on host `127.0.0.1:5432`;
- `migrate` exits successfully after applying migrations;
- `web` is healthy on `http://127.0.0.1:8000`.

## API access

Open these local endpoints after the stack is healthy:

- health: `http://127.0.0.1:8000/health/`;
- Swagger UI: `http://127.0.0.1:8000/api/docs/`;
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`;
- Django Admin: `http://127.0.0.1:8000/admin/`.

The API requires `Authorization: Bearer <access-token>` except for token, schema, Swagger, and health routes. Obtain a token with `POST /api/v1/auth/token/`, then use the raw access token in Swagger's authorization dialog. Do not copy tokens or credentials into version control, issue discussions, or screenshots.

`GET /health/` is a database-aware operational-health endpoint. A `200` response with `{"status":"ok"}` confirms Django can query PostgreSQL; a `503` response with `{"status":"unhealthy"}` means database-backed requests are not ready.

## Development and validation

For host-based validation, start PostgreSQL and run the following from `app/`:

```powershell
uv sync --locked --all-groups
docker compose up -d --wait --wait-timeout 60 db
uv lock --check
uv run python --version
uv run python -m django --version
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate --noinput
uv run pytest
uv run python manage.py spectacular --validate --file .tmp-schema.yml
```

Inspect the generated schema if needed, then remove `.tmp-schema.yml`. A direct development server is available through `uv run python manage.py runserver` when PostgreSQL is available.

## Continuous integration

The `CI` workflow runs for pull requests targeting `main` and for pushes to `main`. It has two stable jobs:

- `Application checks` validates the lockfile, locked dependencies, formatting, linting, Django checks, migration drift, PostgreSQL-backed tests, and the OpenAPI schema;
- `Container build` validates Compose, builds `aws-django-ecs-platform-app:local`, and verifies the non-root image user without starting or publishing the image.

Pull requests must pass both `Application checks` and `Container build`. The workflow does not publish images, deploy, or access AWS resources.

## Container operations

From `app/`:

```powershell
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
docker compose ps --all
docker compose logs --follow web
docker compose run --rm migrate
docker compose run --rm web python manage.py createsuperuser
docker compose exec web id
curl.exe --fail --show-error http://127.0.0.1:8000/health/
```

There is no source bind mount or autoreload. Rebuild the image after source or dependency changes, then recreate the stack. The runtime image excludes development dependencies, test source, and the host virtual environment.

To stop services while preserving database data:

```powershell
docker compose stop
docker compose down
```

The following command is destructive: it permanently deletes the named PostgreSQL volume and all local database data.

```powershell
docker compose down --volumes --remove-orphans
```

## Known limitations

- Static-file handling is not production-ready; Admin styling and offline Swagger assets are not guaranteed through the current runtime.
- AWS infrastructure, image publication, and deployment are not implemented.
- The health endpoint checks database readiness rather than acting as a pure process-liveness endpoint.

## Planned capabilities

- Terraform-managed AWS infrastructure;
- ECR image publication;
- ECS Fargate deployment;
- environment-specific configuration;
- observability;
- security hardening.
