# TASK-001: Establish the Django Project Foundation

## Status

Complete.

## Objective

Create the smallest maintainable Django project foundation for future task-management development.

The task establishes the local Python application structure under `app/`, dependency management, environment-based settings, a minimal custom user model, PostgreSQL through Docker Compose, and basic automated tests.

## Required scope

- select and document a supported Python version;
- select and document a supported Django version;
- select a Python dependency-management approach;
- create the minimal Django project;
- place Django project configuration in `app/config/` and domain applications in `app/apps/`;
- create a minimal custom user model based on `AbstractUser` before the initial migration;
- configure settings through environment variables;
- configure PostgreSQL as the only normal application database;
- provide a local PostgreSQL 17 service through Docker Compose;
- provide a safe example environment file without real secrets;
- add a basic test framework, an Admin smoke test, and custom-user validation;
- add formatting and linting foundations appropriate for Python;
- document local setup and validation commands;
- keep the project runnable without implementing business-domain models.

## Explicitly out of scope

Do not add Project, Membership, or Task models; REST endpoints; JWT; Django application containerization; an application Dockerfile; AWS; Terraform; GitHub Actions; Celery; Redis; email; frontend code; Kubernetes; production settings; or a large boilerplate with unrelated features.

Docker is permitted only for the local PostgreSQL development service in `app/compose.yaml`.

## Planning questions Codex must answer

Before editing, propose:

1. Python and Django versions;
2. dependency-management tool and rationale;
3. settings layout;
4. environment-variable library;
5. test, formatter, and linter tools;
6. expected file tree;
7. validation commands;
8. risks and ambiguities;
9. whether an open-source foundation should be adapted and what attribution is required;
10. the `app/` monorepo layout and minimal custom user model;
11. the local PostgreSQL Compose design.

Wait for approval after presenting the plan.

## Acceptance criteria

- Django starts with documented local configuration;
- no real secret is committed;
- PostgreSQL configuration comes from environment variables;
- PostgreSQL 17 runs locally through a health-checked Compose service with persistent named storage;
- a minimal `users.User` model exists before the initial database migration;
- a smoke test passes;
- PostgreSQL-backed custom-user validation passes;
- formatting and linting pass;
- dependencies are pinned or locked reproducibly;
- README describes only implemented capabilities;
- implementation remains limited to the foundation;
- Codex reports files changed and commands executed.

## Implementation decisions

- Python 3.13 is selected through `app/.python-version` and `requires-python = ">=3.13,<3.14"`.
- Django uses the 5.2 LTS series.
- uv manages `app/.venv` and the committed `app/uv.lock`.
- Django lives under `app/`, with project configuration in `config/` and domain applications in `apps/`.
- The Python import path for the users application is `apps.users`, its Django label is `users`, and the configured model is `users.User`.
- `users.User` subclasses `AbstractUser` without additional fields.
- django-environ loads typed settings while preserving process-environment precedence.
- PostgreSQL is the only normal database and PostgreSQL 17 runs through the local `db` Compose service.
- pytest and pytest-django provide tests; Ruff provides formatting and linting.
- No third-party project foundation is adapted.

## Validation commands

Run Python and Compose commands from `app/`:

```text
uv lock --check
uv sync --locked --all-groups
uv run python --version
uv run python -m django --version
docker compose config --quiet
docker compose up -d --wait --wait-timeout 60 db
docker compose ps
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run python manage.py showmigrations users --plan
uv run pytest
```

Run repository checks from the root:

```text
git diff --check
git check-ignore app/.env
git status --short
```

## Suggested commit

```text
chore: establish the Django project foundation
```
