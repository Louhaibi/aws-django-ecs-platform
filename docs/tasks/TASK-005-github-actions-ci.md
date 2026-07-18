# TASK-005: Add GitHub Actions Continuous Integration

## Status

Ready for planning. Do not implement until the proposed plan is reviewed and approved.

## Objective

Add a secure, reproducible GitHub Actions CI workflow that validates every pull request targeting `main` and every push to `main`.

Automate:

- uv lock validation and locked dependency installation;
- Ruff formatting and linting;
- Django system checks;
- migration-drift detection;
- PostgreSQL-backed tests;
- OpenAPI schema validation;
- Docker Compose configuration validation;
- Docker application-image build.

No deployment, AWS credentials, production secrets, image publication, or repository mutation is allowed.

## Current baseline

TASK-001 through TASK-004 are complete. The repository uses Python 3.13, Django 5.2, uv, PostgreSQL 17, DRF/JWT/OpenAPI, a digest-pinned non-root Docker image, Compose services for `db`, `migrate`, and `web`, and a PostgreSQL-backed pytest suite.

## Git history and merge policy

From TASK-005 onward:

- use one dedicated feature branch per task;
- keep a small number of meaningful commits;
- open one pull request;
- merge using **Create a merge commit**;
- do not squash or rebase the PR;
- delete the feature branch after merge if desired.

Desired history:

```text
*   Merge pull request #... from feature/task-005-github-actions-ci
|\
| * docs: define GitHub Actions CI task
| * ci: add application validation workflow
| * ci: add container build validation
| * docs: complete GitHub Actions CI task
|/
*   previous main commit
```

Do not require linear history.

## Workflow triggers

Run on:

```yaml
pull_request:
  branches: [main]
push:
  branches: [main]
workflow_dispatch:
```

Policy:

- feature branch without PR: local checks;
- PR to `main`: CI only;
- push to `main`: final CI on merged result;
- deployment workflows: future tasks.

Avoid unrestricted feature-branch `push` triggers that duplicate PR runs.

## Concurrency

Use a safe concurrency group that separates unrelated PR and `main` runs and cancels obsolete runs for the same ref:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

Codex must verify the exact expression and explain it.

## Permissions and security

Declare:

```yaml
permissions:
  contents: read
```

Requirements:

- do not use `pull_request_target`;
- no write permissions;
- no AWS/OpenAI/production credentials;
- safe disposable CI-only Django, JWT, PostgreSQL, and Compose values;
- no secret values printed;
- no repository mutation.

## Action pinning

Use official/trusted actions only. Prefer full commit-SHA pins with release comments.

Evaluate and verify from authoritative upstream repositories:

- `actions/checkout`;
- `actions/setup-python`, if needed;
- `astral-sh/setup-uv`;
- `docker/setup-buildx-action`, if needed;
- `docker/build-push-action`, if needed.

Do not invent SHAs. Stop for review if authoritative verification is not possible.

## Python and uv

- use Python 3.13, either from `app/.python-version` or an exact approved patch;
- use the official Astral setup action;
- match the approved uv toolchain where practical;
- run `uv lock --check`;
- run `uv sync --locked --all-groups`;
- cache uv downloads, not `.venv`;
- invalidate cache using `app/uv.lock`;
- never commit `.venv`.

## PostgreSQL service

The application job must use PostgreSQL 17 as a GitHub Actions service container.

Requirements:

- explicit image tag;
- disposable DB/user/password;
- `pg_isready` health check;
- host job connects through `127.0.0.1`;
- use PostgreSQL, never SQLite;
- no Compose dependency for test DB unless justified.

## Stable jobs and checks

Recommended workflow name:

```text
CI
```

Recommended job/check names:

```text
Application checks
Container build
```

### Application checks

Run from `app/`:

```bash
uv lock --check
uv sync --locked --all-groups
uv run python --version
uv run python -m django --version
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run python manage.py migrate
uv run pytest
uv run python manage.py spectacular --validate --file .tmp-ci-schema.yml
```

Remove the temporary schema file or write it outside the tracked workspace.

### Container build

At minimum:

```bash
docker compose config --quiet
docker compose build
```

Provide safe CI-only interpolation values. Do not print full interpolated Compose config.

The job must fail for an invalid Dockerfile, unresolved immutable base reference, lock mismatch in the image build, or invalid Compose configuration.

A non-root image metadata assertion is desirable.

Do not push an image and do not deploy.

## Caching

Approved direction:

- cache uv downloads;
- recreate `.venv` from `uv.lock`;
- optionally use GitHub Actions cache backend for Docker Buildx;
- cache miss must not fail;
- caches must contain no credentials or `.env`.

## Timeouts

Set explicit job timeouts that cover PostgreSQL startup, the full test suite, and a first Docker build without allowing unlimited execution. Codex must propose exact values.

## Failure-mode evidence

Before completion, prove safely that:

- a Ruff violation fails `Application checks`;
- a failing test fails `Application checks`;
- a broken Dockerfile or Compose config fails `Container build`.

Use temporary branch commits/PR updates or another reversible method. Restore valid code afterward. Do not merge broken code into `main`.

## Branch protection after first successful run

Document these GitHub rules for `main`:

- require pull request;
- require `Application checks`;
- require `Container build`;
- require conversation resolution;
- block force pushes;
- block deletion;
- allow merge commits;
- do not require linear history;
- do not require external approval while there is one contributor.

Repository-setting automation is out of scope.

## Future CI/CD policy

TASK-005 implements CI only.

Future policy:

- feature branches: local checks, no deployment;
- PRs to `main`: CI and container build only;
- push to `main`: final CI, later image publication and optional staging deployment;
- production: reviewed version tag/GitHub Release or manual dispatch, protected `production` environment, approval, deploy exact previously tested image digest.

## Documentation

Update:

- `README.md`;
- `CONTRIBUTING.md`;
- `docs/tasks/TASK-005-github-actions-ci.md`;
- `docs/PROJECT-ROADMAP.md` only after completion.

The permanent record must include triggers, jobs, action pins, permissions, concurrency, CI values, PostgreSQL design, commands, caching, timeouts, check names, branch rules, merge-commit policy, passing and failing evidence, limitations, and future CI/CD policy.

After completion:

- TASK-005 → Complete;
- TASK-006 → Next.

## Out of scope

No AWS, OIDC/IAM, ECR, ECS, Terraform, deployments, production environments, releases/tags, Dependabot, CodeQL, package publication, branch-rule automation, or third-party CI.

## Planning questions

Codex must answer:

1. one workflow or multiple;
2. exact triggers;
3. concurrency expression;
4. permissions;
5. stable names;
6. actions and verified SHA pins;
7. Python strategy;
8. uv/cache strategy;
9. PostgreSQL service;
10. CI environment;
11. command order;
12. schema cleanup;
13. container build approach;
14. Docker caching;
15. job dependencies;
16. timeouts;
17. shell/error behavior;
18. branch protection;
19. merge-commit policy;
20. safe failure testing;
21. file tree;
22. documentation;
23. risks;
24. future CI/CD policy.

## Acceptance criteria

- CI runs on PRs to `main` and pushes to `main`;
- obsolete runs cancel safely;
- read-only permissions;
- PostgreSQL 17, not SQLite;
- lock, Ruff, Django, migration, tests, schema checks run;
- Compose validates and image builds without push;
- no AWS or production secret;
- stable required-check names;
- representative failures are detected;
- valid workflow passes;
- merge-commit policy is documented;
- no commit or push until review.

## Suggested meaningful commits

```text
docs: define GitHub Actions CI task
ci: add application validation workflow
ci: add container build validation
docs: complete GitHub Actions CI task
```
