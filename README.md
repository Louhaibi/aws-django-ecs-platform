# AWS Django ECS Platform

A production-oriented cloud and platform engineering portfolio project built around a Django task-management API.

## Current implementation

TASK-001 establishes the application foundation under `app/`:

- Python 3.13 selected and managed through uv;
- Django 5.2 LTS with reproducible dependencies in `uv.lock`;
- environment-based Django settings with no SQLite fallback;
- PostgreSQL 17 for local development through Docker Compose;
- a minimal custom `users.User` model based on `AbstractUser`;
- Django Admin;
- pytest and pytest-django tests;
- Ruff formatting and linting.

The task-management domain, REST API, JWT authentication, application container, AWS infrastructure, and delivery workflows are not implemented yet.

## Repository layout

```text
.
├── app/                  # Django application and local PostgreSQL service
│   ├── apps/             # Domain Django applications
│   ├── config/           # Django project configuration
│   ├── tests/            # Project-level tests
│   ├── compose.yaml      # Local PostgreSQL only
│   ├── pyproject.toml    # Dependencies and tool configuration
│   └── uv.lock           # Exact dependency resolution
└── docs/                 # Charter, decisions, and task specifications
```

## Prerequisites

- uv;
- Docker Desktop running Linux containers with Docker Compose v2;
- Git.

uv selects Python 3.13 from `app/.python-version` and creates `app/.venv`. Do not use an unrelated system Python environment for this project.

## Local setup

Run application and Compose commands from `app/`:

```powershell
Set-Location app
Copy-Item .env.example .env
uv sync --locked --all-groups
docker compose config --quiet
docker compose up -d --wait --wait-timeout 60 db
uv run python manage.py migrate
uv run pytest
```

The committed `.env.example` contains deliberately unsafe local-development values. Replace them in your ignored `.env` when needed, and keep `POSTGRES_*` values consistent with `DATABASE_URL`. URL-encode reserved characters if you choose a database password that contains them.

For an ordinary subsequent database start, the shorter command is:

```powershell
docker compose up -d db
```

Use `docker compose ps` and wait for the service to report `healthy` before running database commands. The `--wait` form in the initial setup does this automatically.

## Run Django

After PostgreSQL is healthy and migrations are applied:

```powershell
uv run python manage.py runserver
```

Django Admin is available at `http://127.0.0.1:8000/admin/`. Create a local administrator only when needed:

```powershell
uv run python manage.py createsuperuser
```

## Validation

From `app/`, with PostgreSQL healthy:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run python --version
uv run python -m django --version
docker compose config --quiet
docker compose ps
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run python manage.py showmigrations users --plan
uv run pytest
```

## Stop the local database

Stop PostgreSQL while retaining its container and named volume:

```powershell
docker compose stop db
```

Remove the container and Compose network while retaining database data:

```powershell
docker compose down
```

To start it again, run `docker compose up -d --wait db`.

The following command deletes the named development volume and all local database data. Run it only when an intentional reset is required:

```powershell
docker compose down --volumes
```

## Project direction

The project will incrementally add the task-management domain, API, container delivery, Terraform-managed AWS infrastructure, CI/CD, security, and observability. Documentation describes only capabilities that currently exist.

See `docs/project-charter.md`, `docs/decisions/`, and `docs/tasks/` for approved scope and architectural decisions.
