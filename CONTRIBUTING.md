# Contributing

Thank you for your interest in contributing to this project.

## Development setup

Install Python 3.13, uv, Docker Desktop with Linux containers and Compose v2, and Git. From `app/`:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
docker compose ps --all
```

The ignored `.env` contains local-only values. Never commit it or put real credentials, keys, or tokens in an image or report. Inside Compose, Django connects to PostgreSQL through hostname `db`; host-based Django commands use `127.0.0.1` in `DATABASE_URL`.

The normal runtime is the full Compose stack. `migrate` must exit successfully before `web` starts. There is no source bind mount or autoreload, so rebuild after source or dependency changes:

```powershell
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
```

Useful operations:

```powershell
docker compose ps
docker compose ps --all
docker compose logs
docker compose logs --follow web
docker compose run --rm migrate
docker compose run --rm web python manage.py shell
docker compose run --rm web python manage.py createsuperuser
docker compose exec web id
```

## Host development and required checks

Use the locked host environment for tests, formatting, linting, and optional direct Django development:

```powershell
uv sync --locked --all-groups
docker compose up -d --wait --wait-timeout 60 db
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run pytest
uv run python manage.py spectacular --validate --file .tmp-task-004-schema.yml
```

Inspect and remove only the temporary schema file after validation. A direct development server remains optional:

```powershell
uv run python manage.py runserver
```

## Container validation

For container-related changes, also run:

```powershell
docker compose config --quiet
docker compose build --pull
docker compose up -d --wait --wait-timeout 120
docker compose ps --all
docker compose logs
docker compose exec web id
docker compose exec web python --version
docker compose exec web python -m django --version
docker compose exec web gunicorn --version
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations --plan
curl.exe --fail --show-error http://127.0.0.1:8000/health/
```

Confirm the image contains expected application files but no `.env`, host `.venv`, test source, or development tools. The runtime user must not be root.

`/health/` is database-aware readiness/operational health. HTTP 200 means Django can query PostgreSQL. HTTP 503 means database-backed requests are not ready and does not necessarily mean Gunicorn has stopped. TASK-004 has no separate liveness route.

## Manual verification

Open Swagger at `http://127.0.0.1:8000/api/docs/`. With a local-only user, obtain a JWT, authorize Swagger, call `GET /api/v1/users/me/`, and perform an authorized API operation. Do not record tokens, passwords, signing keys, or credentials.

For persistence, create a disposable project, record only its numeric ID, and confirm it is retrievable. Then run:

```powershell
docker compose down
docker compose up -d --wait --wait-timeout 120
```

Confirm `db` and `web` are healthy, `migrate` exited successfully, and the same project ID and name remain retrievable. Report whether the disposable record was deleted.

Every pull request should state how to start the services, what was opened or called, the expected behavior, safe stop steps, and whether local data remains.

## Development workflow

1. Update `main` and create a focused feature branch.
2. Keep changes limited to one purpose.
3. Add or update focused tests.
4. Update documentation for behavior or workflow changes.
5. Run host and relevant container checks.
6. Review the complete diff before opening a pull request.

Use clear commit prefixes such as `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `ci`, or `infra`.

## Safe shutdown and repository hygiene

```powershell
# Retains containers and data.
docker compose stop

# Removes containers/network and preserves postgres_data.
docker compose down
```

This command is an explicitly destructive reset and permanently deletes all local PostgreSQL data:

```powershell
docker compose down --volumes --remove-orphans
```

Do not commit `.env` files, credentials, tokens, virtual environments, caches, coverage output, local databases, generated test data, or editor artifacts.
