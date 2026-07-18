# TASK-004: Containerize Django and Complete the Local Docker Compose Stack

## Status

Complete

## Objective

Containerize the Django application and run the complete local platform through Docker Compose.

The resulting local stack must include:

- PostgreSQL;
- the Django application;
- reliable startup ordering;
- safe migration handling;
- container health checks;
- non-root application execution;
- persistent database storage;
- documented developer workflows.

The implementation must prepare the application image for later use in Amazon ECR and ECS Fargate without introducing AWS infrastructure in this task.

## Current baseline

TASK-001 through TASK-003 are complete.

The repository currently includes:

- Python 3.13;
- Django 5.2 LTS;
- uv dependency management;
- PostgreSQL 17;
- an existing PostgreSQL Compose service;
- a versioned REST API;
- JWT authentication;
- Swagger/OpenAPI documentation;
- PostgreSQL-backed pytest coverage.

TASK-004 must preserve all current behavior.

## Required outcomes

After implementation, a developer must be able to run:

```powershell
docker compose up --build
```

and obtain a healthy local stack where:

- PostgreSQL starts successfully;
- Django waits for PostgreSQL readiness;
- migrations are applied safely;
- Django starts successfully;
- the API is reachable;
- Swagger UI is reachable;
- the application container runs as a non-root user;
- logs are visible through Docker Compose;
- stopping the stack does not delete PostgreSQL data.

## Container image requirements

Create a production-oriented application image.

The planning phase must decide and explain:

- base image;
- single-stage versus multi-stage build;
- how uv is installed and used;
- dependency installation strategy;
- whether development dependencies are included in the runtime image;
- image-layer caching strategy;
- application working directory;
- file ownership;
- non-root user and group creation;
- Python runtime settings;
- static-file expectations;
- startup command;
- health-check mechanism.

The image must:

- pin the Python major/minor version consistently with the project;
- install from the committed lockfile;
- fail if the lockfile is inconsistent;
- avoid copying local virtual environments, Git metadata, secrets, caches, and test artifacts;
- avoid running Django as root;
- use deterministic dependency installation;
- be reusable later by ECR and ECS;
- not contain local `.env` values;
- not bake secrets into image layers.

## Dockerfile

Add an application Dockerfile under `app/`.

Preferred path:

```text
app/Dockerfile
```

The plan must explain all important instructions and layer ordering.

The Dockerfile should support:

- reproducible builds;
- efficient rebuilds when only source code changes;
- an explicit non-root runtime user;
- appropriate environment variables such as unbuffered Python output;
- an application startup command appropriate for the current stage.

Do not add Nginx in TASK-004.

The planning phase must explicitly decide whether local Compose runs Django through:

- Django's development server; or
- a production WSGI server such as Gunicorn.

Prefer a design that prepares the image for ECS while still supporting local development clearly. If Gunicorn is introduced, justify it and define whether it is a runtime dependency.

## `.dockerignore`

Add:

```text
app/.dockerignore
```

It must exclude at least:

- `.venv`;
- `.env`;
- Python caches;
- pytest caches;
- Ruff caches;
- coverage artifacts;
- Git metadata where applicable;
- editor and OS artifacts;
- temporary OpenAPI files;
- local databases or generated files;
- temporary TASK output reports if they can appear in the build context.

Do not exclude required application source, migrations, `pyproject.toml`, or `uv.lock`.

## Startup and migration handling

The stack must not start Django before PostgreSQL is ready.

The planning phase must compare reasonable approaches and select one:

- Compose health-based dependency plus a startup script;
- an explicit database wait loop;
- a dedicated one-off migration service;
- another simple and reliable approach.

Requirements:

- migrations are applied before the application begins serving traffic;
- startup fails visibly if migration fails;
- repeated startup is safe;
- the approach is suitable for local Compose;
- the documentation clearly states that ECS migration execution will be reconsidered later;
- no destructive database reset occurs automatically.

Avoid a complicated orchestration framework.

## Health endpoint

Add a lightweight application health endpoint suitable for:

- Docker Compose health checks now;
- ECS/ALB health checks later.

Preferred route:

```text
/health/
```

The planning phase must decide whether the endpoint checks:

- only Django process liveness; or
- both application liveness and database connectivity.

A database-aware readiness check is preferred if it remains lightweight and returns controlled responses.

Requirements:

- no authentication required;
- no sensitive data returned;
- successful response uses `200`;
- unavailable dependency uses a controlled non-`200` response;
- response format is simple and stable;
- OpenAPI inclusion or exclusion is intentional and documented;
- automated tests cover healthy and database-unavailable behavior where practical.

Do not expose configuration, credentials, version internals, or stack traces.

## Docker Compose

Extend the existing `app/compose.yaml`.

Required services:

- `db`;
- `web` or another clearly named Django application service.

The application service must define:

- build context and Dockerfile;
- environment configuration;
- PostgreSQL dependency;
- port mapping for local access;
- health check;
- restart behavior appropriate for local development;
- named-volume behavior where needed;
- clear command or entrypoint behavior.

The database service must retain:

- PostgreSQL 17;
- persistent named volume;
- health check;
- local development credentials sourced from environment configuration.

The plan must decide whether source code is bind-mounted into the Django container.

If bind mounts are used:

- explain whether reload behavior is supported;
- avoid overwriting the container's installed environment;
- keep the production image behavior understandable.

If bind mounts are not used:

- explain the rebuild workflow after source changes.

Do not add a second Compose file unless there is a clear approved reason.

## Environment configuration

Update `app/.env.example` as required.

Requirements:

- no production secret or real credential;
- Compose variables are documented;
- Django uses the PostgreSQL service hostname inside Compose;
- host-based local commands remain understandable;
- JWT signing key remains required;
- configuration differences between host execution and container execution are explicit.

The plan must determine whether to use:

- one `DATABASE_URL` value for container execution;
- Compose interpolation variables;
- a separate container-specific variable;
- another minimal approach.

Avoid making `.env.example` misleading for either host or container use.

## Local development workflow

Document exact commands for:

- building images;
- starting the full stack;
- starting in detached mode;
- viewing service status;
- viewing logs;
- following Django logs;
- running migrations manually;
- opening a Django shell;
- creating a superuser;
- running tests;
- rebuilding after dependency changes;
- rebuilding after source changes;
- stopping services;
- removing containers without deleting data;
- intentionally deleting local data;
- checking container user identity;
- checking health;
- accessing Swagger.

The documentation must clearly distinguish:

```powershell
docker compose stop
```

from destructive volume removal.

## Tests and validation

Add focused tests where application behavior changes.

Required automated coverage includes:

- public health endpoint returns `200` when dependencies are healthy;
- health response contains only approved fields;
- database connectivity failure produces a controlled unhealthy response where practical;
- existing API behavior remains unchanged.

Container validation must include:

```powershell
docker compose config
docker compose build
docker compose up -d --wait
docker compose ps
docker compose logs
```

Also verify from the host:

- `/health/`;
- `/api/docs/`;
- one protected API endpoint;
- token obtain;
- authenticated API access.

Verify inside the application container:

- effective user is not root;
- expected application files exist;
- Python and Django versions are correct;
- migrations are applied;
- no `.env` file is baked into the image;
- no local `.venv` is copied into the image.

Run the existing project checks:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv run python manage.py spectacular --validate
```

The planning phase may refine exact container commands, but must preserve equivalent validation.

## Documentation

Update:

- `README.md`;
- `CONTRIBUTING.md` where development commands change;
- `docs/tasks/TASK-004-django-containerization.md`;
- `docs/PROJECT-ROADMAP.md` status after completion.

The permanent TASK-004 record must include:

- final image design;
- Dockerfile decisions;
- non-root user design;
- Compose service definitions;
- health endpoint behavior;
- migration/startup strategy;
- environment handling;
- local commands;
- automated validation;
- manual container verification;
- limitations and deferred ECS decisions.

Create an ADR only if the planning phase identifies a durable cross-project container architecture decision that cannot be adequately recorded in this task.

## Explicitly out of scope

Do not add:

- AWS resources;
- Terraform;
- ECR;
- ECS;
- GitHub Actions;
- deployment automation;
- Nginx;
- Traefik;
- Kubernetes;
- Celery;
- Redis;
- WebSockets;
- background jobs;
- custom domain or TLS;
- CloudWatch;
- production secrets;
- database backups;
- autoscaling;
- blue/green deployments.

## Planning questions Codex must answer

Before editing, explain:

1. exact Docker image strategy;
2. base image and version;
3. single-stage versus multi-stage build;
4. uv installation and locked dependency installation;
5. runtime versus development dependency handling;
6. non-root user implementation;
7. Dockerfile layer ordering and caching;
8. `.dockerignore` contents;
9. local server choice: runserver versus Gunicorn;
10. startup and migration strategy;
11. PostgreSQL readiness handling;
12. health endpoint design;
13. Compose service definitions;
14. source bind-mount decision;
15. environment-variable strategy;
16. port and hostname behavior;
17. persistence and safe shutdown behavior;
18. container test strategy;
19. exact validation commands;
20. manual verification workflow;
21. expected file tree;
22. documentation changes;
23. security risks and known limitations;
24. implications for later ECR/ECS tasks.

For each important choice:

- explain why it is suitable;
- mention a reasonable alternative;
- identify local-development tradeoffs;
- avoid prematurely implementing AWS concerns.

Use authoritative current documentation for version-sensitive Docker, Compose, uv, Django, and server behavior.

## Acceptance criteria

- Application Dockerfile exists.
- `.dockerignore` exists.
- Django runs as a non-root container user.
- PostgreSQL and Django run together through Docker Compose.
- PostgreSQL readiness is handled safely.
- migrations complete before application traffic is served.
- `/health/` works and exposes no sensitive information.
- application and database services become healthy.
- Swagger is reachable through the containerized stack.
- JWT obtain and authenticated API access work through the containerized stack.
- database data survives ordinary stop/start cycles.
- destructive reset requires an explicit command.
- no `.env`, secret, local virtual environment, or Git metadata is baked into the image.
- existing tests remain green.
- container build and runtime verification are documented.
- no AWS, Terraform, CI/CD, or unrelated service is introduced.
- no commit or push occurs until review.

## Suggested commit message

```text
feat: containerize django application
```

## Approved design and implementation record

This section records the complete approved TASK-004 design, implemented result, and completed verification evidence.

### Immutable image and build design

The image is a multi-stage Linux image. During implementation, the requested tags were inspected through the local Docker engine with `docker buildx imagetools inspect`, and the immutable references were re-inspected to ensure each selected value was the top-level multi-platform OCI image-index digest—not a layer or architecture-specific child digest:

```text
python:3.13.14-slim-bookworm@sha256:9d7f287598e1a5a978c015ee176d8216435aaf335ed69ac3c38dd1bbb10e8d64
ghcr.io/astral-sh/uv:0.11.29@sha256:eb2843a1e56fd9e30c7276ce1a52cba86e64c7b385f5e3279a0e08e02dd058fc
```

The named `uv` stage supplies `/uv` and `/uvx` to a Python builder stage. The builder sets `UV_COMPILE_BYTECODE=1`, `UV_LINK_MODE=copy`, and `UV_PYTHON_DOWNLOADS=never`, then runs:

```text
uv sync --locked --no-dev --no-install-project
```

Only `pyproject.toml` and `uv.lock` are copied before dependency installation, so source-only changes reuse the locked-dependency layer. A BuildKit cache mount retains uv downloads between builds. The runtime stage uses the same pinned Python reference and receives only `/app/.venv` plus application source. Runtime dependencies include Gunicorn 26.0.0; Ruff, pytest, pytest-django, uv itself, and other development dependencies are excluded. The committed lockfile remains authoritative, and an inconsistent lock fails the build.

The runtime creates group and user `app` with fixed GID/UID 10001, no home, and a nologin shell. `/app`, its virtual environment, and source are owned by that identity, and the final image declares `USER 10001:10001`. Python is unbuffered, bytecode writes are disabled at runtime, `/app/.venv/bin` is on `PATH`, and the working directory is `/app`.

Gunicorn is used instead of Django `runserver` because the same image can later be promoted to ECR/ECS. It binds `0.0.0.0:8000`, runs two sync workers, logs access and errors to standard streams, and disables Gunicorn 26's optional control socket because the deliberately home-less user cannot and need not create it. Gunicorn is PID 1 and receives container stop signals directly. Worker count and timeout tuning remain later measured decisions.

The exact build-context exclusions are:

```text
.env
.env.*
.venv/
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
tests/
.coverage
.coverage.*
coverage.xml
htmlcov/
build/
dist/
*.egg-info/
*.log
db.sqlite3
*.sqlite3
staticfiles/
media/
.git/
.gitignore
.codex/
.vscode/
.idea/
.DS_Store
Thumbs.db
*.swp
*~
compose*.yaml
compose*.yml
.tmp-*
TASK-*-plan-output.md
TASK-*-output.md
```

Required source, migrations, `pyproject.toml`, and `uv.lock` remain in the context. Environment files, including the example, are excluded because Compose consumes the host example only when creating an ignored `.env`; the runtime source copy includes no environment file.

Alternatives rejected for this task were a single-stage image, installing uv from the network in a `RUN` instruction, including dev tools in runtime, using root, and running `runserver`. Those options would reduce separation or fidelity and make the resulting artifact less suitable for later container deployment.

### Compose services, startup, and persistence

`compose.yaml` defines one application image, `aws-django-ecs-platform-app:local`, used by two application services:

- `db` uses the existing `postgres:17` convention, reads local `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`, publishes `127.0.0.1:${POSTGRES_PORT:-5432}:5432`, mounts `postgres_data:/var/lib/postgresql/data`, and checks readiness over TCP with `pg_isready` on `127.0.0.1`;
- `migrate` uses the application image and runs `python manage.py migrate --noinput` only after `db` is healthy. It has no published port and must exit successfully;
- `web` builds the shared image, waits for both a healthy database and successful migration service, publishes `127.0.0.1:${WEB_PORT:-8000}:8000`, and uses the image's Gunicorn command.

Docker Compose reads the ignored `app/.env` file for interpolation. The Compose file then passes only the selected settings in each service's explicit `environment` mapping and constructs the application containers' `DATABASE_URL` with service hostname `db`. Unrelated values from the local environment file are not automatically passed into the application containers, and no `.env` file is copied into or baked into the image. Restart policy is `no`, appropriate for visible local failures, and web has a 30-second stop grace period. The web health check uses Python's standard library to request `/health/`; no diagnostic package is added to runtime.

There is no source bind mount or second Compose file. Source and dependency changes require `docker compose build` followed by stack recreation. This is slower than autoreload but produces consistent Windows, WSL 2, Docker Desktop, and eventual ECS behavior without masking image contents or overwriting the Linux virtual environment.

Migrations are deliberately a separate, idempotent one-shot service. A migration failure prevents web startup and remains visible through Compose status/logs. No database wait script or automatic reset is used. ECS must later run migrations as a controlled one-off deployment task; Compose dependency semantics must not be copied to a replicated ECS service.

Host ports are loopback-only. From Windows or WSL 2, use `127.0.0.1:8000` and `127.0.0.1:5432`; `db` is resolvable only inside the Compose network. An ignored host-development `.env` uses a host `DATABASE_URL`; Compose overrides it for application containers. The example password is URL-safe because Compose interpolates it into a URL.

Ordinary `docker compose stop` retains containers and the volume. Ordinary `docker compose down` removes containers and the network but preserves `postgres_data`. Only the following explicitly destructive reset removes all local database data:

```powershell
docker compose down --volumes --remove-orphans
```

That destructive command was not run during implementation validation.

### Operational-health contract

TASK-004 adds exactly one public, GET-only route: `GET /health/`. It is a database-aware readiness/operational-health endpoint, not pure process liveness. The view performs `SELECT 1` through Django's configured database connection, catches only `django.db.DatabaseError`, and returns no configuration, version, exception, or credential data.

| Condition | Status | Exact JSON | Meaning |
| --- | ---: | --- | --- |
| PostgreSQL query succeeds | 200 | `{"status":"ok"}` | Django can currently query PostgreSQL and is ready for database-backed requests. |
| Django raises `DatabaseError` | 503 | `{"status":"unhealthy"}` | The application is not ready for database-backed requests. Gunicorn may still be running. |
| Non-GET request | 405 | Django method-not-allowed response | The endpoint is read-only. |

The route is intentionally excluded from the REST API schema and Swagger because it is an operational route, not application API surface. Docker Compose uses it as the web readiness check. ECS/ALB design may later split process liveness and readiness; no extra route is added now.

Focused tests assert the exact 200 and 503 fields, JSON content type, controlled mocked `OperationalError` behavior without exception leakage, GET-only behavior, and OpenAPI exclusion. A real readiness transition was also verified: PostgreSQL was stopped, `/health/` returned HTTP 503 with `{"status":"unhealthy"}` while the web container remained running, PostgreSQL was restarted and became healthy, and the endpoint returned HTTP 200 with `{"status":"ok"}`.

### Developer commands

```powershell
# Configure, build, and start
Copy-Item .env.example .env
docker compose config --quiet
docker compose build --pull
docker compose up -d --wait --wait-timeout 120

# Observe
docker compose ps
docker compose ps --all
docker compose logs
docker compose logs --follow web

# Operate Django
docker compose run --rm migrate
docker compose run --rm web python manage.py shell
docker compose run --rm web python manage.py createsuperuser

# Inspect runtime
docker compose exec web id
docker compose exec web python --version
docker compose exec web python -m django --version
docker compose exec web gunicorn --version
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations --plan

# Check host endpoints
curl.exe --fail --show-error http://127.0.0.1:8000/health/
curl.exe --include http://127.0.0.1:8000/api/v1/users/me/

# Stop safely
docker compose stop
docker compose down
```

Host lint/test development remains:

```powershell
uv sync --locked --all-groups
docker compose up -d --wait --wait-timeout 60 db
uv run python manage.py migrate
uv run python manage.py runserver
```

### Automated and container verification results

Implementation-time results on 2026-07-18:

- `uv lock --check`: passed, 30 packages resolved;
- `uv sync --locked --all-groups`: passed;
- Python 3.13.14 and Django 5.2.16 verified;
- `ruff format --check .`: passed for 52 files;
- `ruff check .`: passed;
- `python manage.py check`: no issues;
- `python manage.py makemigrations --check --dry-run`: passed with no migration generated;
- `python manage.py migrate`: passed;
- `pytest`: 76 passed in 248.85 seconds;
- `spectacular --validate`: passed and its temporary schema file was removed;
- `docker compose config --quiet`: passed;
- `docker compose build --pull`: passed using both immutable image references;
- `docker compose up -d --wait --wait-timeout 120`: passed;
- `db` and `web`: healthy; `migrate`: exited 0 with no migrations pending;
- runtime identity: `uid=10001(app) gid=10001(app)`;
- runtime versions: Python 3.13.14, Django 5.2.16, Gunicorn 26.0.0;
- image config: `USER 10001:10001`, workdir `/app`, expected Gunicorn command;
- fresh startup logs: two Gunicorn sync workers, no control-socket error, and clean migration completion;
- host `/health/`: 200 with exact healthy JSON;
- host `/api/docs/`: 200;
- unauthenticated `/api/v1/users/me/`: 401 as expected;
- database-outage readiness transition: controlled 503 while Gunicorn remained running, then 200 after database recovery.

The runtime deliberately has no `uv` executable. This confirms the runtime-only dependency strategy rather than a failed requirement; uv remains confined to the build stage and host development environment.

### Completed manual verification

Manual verification completed successfully with local-only data and credentials:

- Docker Compose `db` and `web` services became healthy;
- the `migrate` service exited successfully with code 0;
- `GET /health/` returned HTTP 200 with `{"status":"ok"}`;
- Swagger UI rendered successfully through the Gunicorn container;
- unauthenticated `GET /api/v1/users/me/` returned HTTP 401;
- JWT token obtain succeeded;
- authenticated `GET /api/v1/users/me/` returned HTTP 200;
- an authenticated project or task endpoint returned HTTP 200;
- a project was retrieved with the same ID and name before and after this ordinary Compose teardown and restart:

  ```powershell
  docker compose down
  docker compose up -d --wait --wait-timeout 120
  ```

- ordinary `docker compose down` preserved the `postgres_data` named volume;
- `docker compose down --volumes` was not run.

No token, password, signing key, database credential, or other sensitive value is recorded.

Observed local limitations:

- `/` intentionally returns HTTP 404 because the project defines no root route;
- Django Admin is functional, but Gunicorn does not serve its CSS because TASK-004 deliberately adds no static-file pipeline;
- `DEBUG` remains enabled only for local development.

TASK-004 does not implement Nginx, WhiteNoise, static-file deployment, AWS, ECR, ECS, or CI/CD.

### Security, operational limitations, and later ECS compatibility

- Committed example secrets are intentionally unsafe local placeholders. Runtime environment metadata is visible to sufficiently privileged local Docker users; later deployment must use managed secrets and least privilege.
- Ports bind only to loopback, but local processes can connect. Gunicorn serves plain HTTP, so local JWTs must not be treated as production-secure; deployed traffic requires TLS.
- Both external image references are immutable and therefore require deliberate digest refresh, vulnerability review, and rebuilds. They do not receive tag updates automatically. The existing `postgres:17` service remains a mutable local-development convention.
- Database-aware health performs a small query on every check and intentionally removes the app from readiness during database outages. It does not prove migration currency or process liveness.
- The non-root image does not yet enforce a read-only root filesystem, dropped capabilities, `no-new-privileges`, custom seccomp, or other later runtime hardening.
- There is no Nginx, WhiteNoise, `collectstatic`, offline Swagger bundle, or production static/media pipeline. Admin styling and Swagger assets under Gunicorn remain a known manual-verification limitation.
- No bind mount means no autoreload. Runtime excludes tests and development tools; host checks validate source while container checks validate the artifact.
- No AWS, ECR, ECS, Terraform, CI/CD, TLS, backups, autoscaling, monitoring, or production secret delivery is implemented.

The resulting image is nevertheless suitable as the input to later ECR/ECS work: it is Linux, immutable, self-contained, non-root, environment-configured, binds `0.0.0.0:8000`, logs to standard streams, receives signals as PID 1, and exposes a stable operational-health contract. Later tasks must decide image scanning/tagging/provenance, digest-based deployment, migration tasks, ALB checks and grace periods, liveness separation, task CPU/memory, Gunicorn sizing, database connection behavior, static assets, read-only filesystem feasibility, and graceful deployment timing.
