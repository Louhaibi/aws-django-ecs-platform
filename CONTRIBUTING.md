# Contributing

## Development setup

Install Python 3.13, uv, Docker Desktop with Linux containers and Compose v2, and Git. From `app/`:

```powershell
Copy-Item .env.example .env
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 120
docker compose ps --all
```

The normal runtime is the Compose stack. The `migrate` service must complete successfully before `web` starts. There is no source bind mount or autoreload, so rebuild after source or dependency changes.

## Environment configuration

Keep `.env` local and out of version control. Do not place real credentials, keys, or tokens in an image, commit, issue, or pull request.

Inside Compose, Django connects to PostgreSQL through hostname `db`. Host-based Django commands must use a database URL that targets `127.0.0.1`. Keep the database settings consistent with the values supplied to Compose.

## Local validation

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
uv run python manage.py spectacular --validate --file .tmp-schema.yml
```

Remove `.tmp-schema.yml` after validation.

## Container validation

For container-related changes, also run from `app/`:

```powershell
docker compose config --quiet
docker compose build --pull
docker image inspect --format '{{.Config.User}}' aws-django-ecs-platform-app:local
docker compose up -d --wait --wait-timeout 120
docker compose ps --all
docker compose exec web id
docker compose exec web python manage.py check
curl.exe --fail --show-error http://127.0.0.1:8000/health/
```

The image inspection result must be `10001:10001`. Confirm that the runtime image does not include `.env`, the host virtual environment, test source, or development tools.

## API verification

Open Swagger at `http://127.0.0.1:8000/api/docs/`. Create or use a local account, obtain a JWT from `POST /api/v1/auth/token/`, authorize Swagger with the raw access token, and call `GET /api/v1/users/me/` plus an authorized project or task operation.

Confirm `/health/` returns `200` when PostgreSQL is available. Do not record tokens, passwords, signing keys, or credentials in project materials.

## Pull request expectations

Use a focused branch and keep commits clear and descriptive. Include relevant tests and documentation changes, then review the complete diff before opening a pull request.

Pull requests must pass both CI checks:

- `Application checks`;
- `Container build`.

Describe relevant validation and any operational impact in the pull request.

## Repository hygiene

Do not commit `.env` files, credentials, tokens, virtual environments, caches, coverage output, local databases, generated test data, or editor artifacts.

## Safe shutdown and reset

To stop services and preserve database data:

```powershell
docker compose stop
docker compose down
```

The following command is destructive and permanently deletes the named PostgreSQL volume and all local database data:

```powershell
docker compose down --volumes --remove-orphans
```
