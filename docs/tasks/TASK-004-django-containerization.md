# TASK-004: Containerize Django and Complete the Local Docker Compose Stack

## Status

Ready for planning. Do not implement until the proposed plan is reviewed and approved.

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
