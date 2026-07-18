# AWS Django ECS Platform

A production-oriented cloud and platform engineering portfolio project built around a Django task-management API.

## Current implementation

TASK-001 through TASK-003 provide the Python 3.13/Django 5.2 application, PostgreSQL-backed project and task domain, Django Admin, JWT-authenticated REST API, Swagger/OpenAPI, pytest, and Ruff.

TASK-004 adds a complete local container stack:

- a reproducible, multi-stage Django image built from digest-pinned Python and uv images;
- a non-root Gunicorn runtime with production dependencies only;
- PostgreSQL 17 with a persistent named volume;
- a one-shot migration service that must succeed before the web service starts;
- a database-aware operational-health endpoint at `/health/`;
- loopback-only host ports and environment-based configuration.

TASK-005 adds GitHub Actions continuous integration with PostgreSQL-backed application validation and a non-publishing container build.

AWS infrastructure, image publication, and deployment workflows are not implemented yet.

## Repository layout

```text
.
|-- .github/
|   `-- workflows/ci.yml # Pull-request and main-branch CI
|-- app/
|   |-- apps/             # Users, projects, tasks, and REST API
|   |-- config/           # Django project configuration and health view
|   |-- tests/            # Project-level tests
|   |-- .dockerignore     # Container build-context exclusions
|   |-- Dockerfile        # Multi-stage non-root Gunicorn image
|   |-- compose.yaml      # PostgreSQL, migration, and web services
|   |-- pyproject.toml    # Dependencies and tool configuration
|   `-- uv.lock           # Exact dependency resolution
`-- docs/                 # Charter, decisions, roadmap, and task records
```

## Prerequisites

- Docker Desktop running Linux containers with Docker Compose v2;
- uv for host-based development checks;
- Git.

Docker Desktop must be running before Compose commands. Windows PowerShell commands below also work from WSL 2 with the equivalent shell syntax. Host access uses `127.0.0.1`; the names `db` and `web` are Compose-network hostnames and are not host URLs.

## Container-first quick start

Run from `app/`:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
docker compose ps
docker compose ps --all
```

The committed example values are deliberately unsafe and local-only. Keep the ignored `.env` file out of Git. `JWT_SIGNING_KEY` is required and separate from `DJANGO_SECRET_KEY`. Keep the `POSTGRES_*` values consistent; Compose constructs the container-only `DATABASE_URL` with hostname `db`. Passwords used in that URL must be URL-safe.

Expected state:

- `db` is healthy on host `127.0.0.1:5432`;
- `migrate` exits successfully after applying migrations;
- `web` is healthy on `http://127.0.0.1:8000`.

Open:

- operational health: `http://127.0.0.1:8000/health/`;
- Swagger UI: `http://127.0.0.1:8000/api/docs/`;
- OpenAPI schema: `http://127.0.0.1:8000/api/schema/`;
- Django Admin: `http://127.0.0.1:8000/admin/`.

`GET /health/` is a database-aware readiness/operational-health endpoint, not pure process liveness. HTTP 200 with `{"status":"ok"}` means Django can query PostgreSQL. HTTP 503 with `{"status":"unhealthy"}` means the application is not ready for database-backed requests; Gunicorn may still be running. TASK-004 adds no separate liveness route.

## Container operations

```powershell
# Build or rebuild after source/dependency changes
docker compose build --pull
docker compose up -d --wait --wait-timeout 120

# Status and logs
docker compose ps
docker compose ps --all
docker compose logs
docker compose logs --follow web

# Application operations
docker compose run --rm migrate
docker compose run --rm web python manage.py shell
docker compose run --rm web python manage.py createsuperuser
docker compose exec web id
curl.exe --fail --show-error http://127.0.0.1:8000/health/
```

There is no source bind mount or autoreload. Rebuild the image after source or dependency changes, then recreate the stack. The runtime image excludes uv, Ruff, pytest, development dependencies, test source, and the host virtual environment.

Gunicorn serves application responses but TASK-004 does not add a production static-file pipeline. Admin styling and offline Swagger assets are therefore not guaranteed through this runtime; static-file handling is deferred.

## Host-based development workflow

Host execution remains supported for tests, linting, and optional `runserver`. In the ignored `.env`, use a host database URL such as `postgresql://...@127.0.0.1:5432/...`, not the Compose-only hostname `db`.

```powershell
uv sync --locked --all-groups
docker compose up -d --wait --wait-timeout 60 db
uv run python manage.py migrate
uv run python manage.py runserver
```

The locked runtime dependency set includes Gunicorn; host development groups additionally include pytest, pytest-django, and Ruff.

## API and Swagger verification

The API requires `Authorization: Bearer <access-token>` except for token, schema, Swagger, and health routes. In Swagger, use `POST /api/v1/auth/token/`, select **Authorize**, paste only the raw access token, and try `GET /api/v1/users/me/` plus an authorized project or task operation. Never copy tokens or local credentials into reports, screenshots, commits, issues, or pull requests.

## Validation

From `app/`, with PostgreSQL healthy:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run python --version
uv run python -m django --version
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate --noinput
uv run pytest
uv run python manage.py spectacular --validate --file .tmp-task-005-schema.yml
docker compose config --quiet
docker compose build --pull
docker image inspect --format '{{.Config.User}}' aws-django-ecs-platform-app:local
```

The image inspection result must be `10001:10001`. Inspect the schema result, then remove only `.tmp-task-005-schema.yml`.

## Continuous integration

The `CI` workflow has two independent, stable jobs:

- `Application checks` installs the locked development environment with Python 3.13.14 and uv 0.11.29, uses a PostgreSQL 17 service, and runs the application commands listed above through schema validation;
- `Container build` validates Compose, builds `aws-django-ecs-platform-app:local` with `--pull`, and verifies the image is configured to run as `10001:10001` without starting or pushing it.

CI runs for pull requests targeting `main`, where GitHub tests the pull request merge ref, and runs again for pushes to `main`, where it validates the committed merge result. A push to a feature branch alone does not run CI; run the local equivalents before opening or updating a pull request. The workflow does not publish images, deploy, use AWS, or use production secrets.

Repository rules for `main` should require both stable checks, `Application checks` and `Container build`. From TASK-005 onward, pull requests must be merged with **Create a merge commit**; squash merging and rebase merging should be disabled where repository settings permit it. This preserves the task branch's small, meaningful commit series under an explicit merge commit.

Future delivery workflows may publish a tested image and optionally deploy staging after a push to `main`. Production deployment must remain a separate reviewed version-tag, GitHub Release, or manually dispatched operation that uses a protected production environment and deploys the exact previously tested image digest. No deployment is implemented by TASK-005.

## Persistence check

After Swagger/JWT access works, create a disposable local project through the authenticated API and record only its numeric ID. Confirm it is retrievable, then run:

```powershell
docker compose down
docker compose up -d --wait --wait-timeout 120
```

Obtain a fresh token if needed and confirm the same ID and project name are still retrievable. This proves ordinary `down` preserves the `postgres_data` named volume. Delete the disposable record afterward if desired.

## Safe stop and reset commands

```powershell
# Stop containers and retain them and all database data.
docker compose stop

# Remove containers/network but preserve postgres_data.
docker compose down
```

The following is an explicitly destructive reset. It permanently deletes the named PostgreSQL volume and all local database data:

```powershell
docker compose down --volumes --remove-orphans
```

Do not use the destructive command during normal validation.

## Project direction

Later tasks add Terraform-managed AWS infrastructure, ECR/ECS delivery, deployment automation, security, and observability. The current container image is designed for later ECR/ECS use, but no AWS capability or deployment is claimed here.

See `docs/project-charter.md`, `docs/decisions/`, and `docs/tasks/` for approved scope and architectural decisions.
