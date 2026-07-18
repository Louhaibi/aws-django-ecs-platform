# TASK-005: Add GitHub Actions Continuous Integration

## Status

Complete

GitHub-hosted success and failure evidence, cleaned feature-branch history, the active `main` ruleset, and repository merge settings have been confirmed.

## Objective

Provide secure, reproducible continuous integration for every pull request targeting `main` and every push to `main`. CI validates the locked Django application against PostgreSQL 17 and validates the production-oriented Compose image build without publishing an image or deploying anything.

TASK-005 does not use AWS, credentials, production secrets, OIDC, environments, artifacts, registries, or deployment services.

## Implemented files and workflow structure

The implementation uses one workflow:

```text
.github/
`-- workflows/
    `-- ci.yml
```

The workflow name is `CI`. One workflow keeps the shared event, permission, concurrency, and runner policy together while its two independent jobs execute in parallel:

| Job ID | Stable job/check name | Purpose |
| --- | --- | --- |
| `application` | `Application checks` | Lock, dependencies, Ruff, Django, migrations, PostgreSQL-backed tests, and schema validation |
| `container` | `Container build` | Compose validation, application-image build, and non-root metadata assertion |

The job names are permanent required-check contracts. Do not casually rename or duplicate them in another workflow.

## Triggers and merge-ref behavior

The workflow uses exactly:

```yaml
on:
  pull_request:
    branches:
      - main
  push:
    branches:
      - main
  workflow_dispatch:
```

For a pull request to `main`, the default checkout tests GitHub's pull-request merge ref. That ref represents the proposed feature branch integrated with the current base branch, so it can detect an integration failure that a feature-head-only run could miss. Checkout is not overridden to the head SHA.

The workflow runs again after a push to `main` because that event validates the actual merge commit that now forms repository history. A passing merge-ref run is strong pre-merge evidence but is not a substitute for validating the committed result after the merge occurs.

A feature-branch push without a pull request does not trigger this workflow. Developers run the documented local equivalents until the single task pull request exists. `workflow_dispatch` is available for an explicitly requested diagnostic run after the workflow exists on the default branch.

There are no path filters, schedules, unrestricted feature-branch push triggers, `pull_request_target`, or `merge_group` trigger. If a merge queue is introduced later, add `merge_group` before making these checks queue requirements.

## Concurrency

The workflow uses exactly:

```yaml
concurrency:
  group: ci-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

`github.workflow` prevents accidental cancellation across differently named workflows. Pull requests use their PR number, so a new commit cancels only an obsolete run for that same PR. Push and manual events fall back to `github.ref`; pushes to `main` therefore cancel only an older `main` run. A manual dispatch on `main` shares the group with a `main` push and can cancel, or be cancelled by, that run. This is an accepted diagnostic-run limitation.

## Permissions and security boundary

The workflow declares only:

```yaml
permissions:
  contents: read
```

Both checkout steps use `persist-credentials: false`, so the workflow token is not left available to later shell or Docker steps. There are no job-level permission overrides, write permissions, secrets, repository mutations, AWS calls, or production values. Proposed source and Docker instructions run only in the ordinary unprivileged `pull_request` context; `pull_request_target` is prohibited.

GitHub-hosted Bash is selected for all `run` steps through workflow defaults. GitHub invokes this shell with fail-fast and pipeline-failure behavior. No step uses `continue-on-error`; a failed command fails its job while the other independent job continues to provide its result. Both jobs have `timeout-minutes: 20`.

## External actions and immutable pins

Only these upstream actions are used, pinned to the approved full release commit with a release comment:

```yaml
actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7.0.0
actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0
astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990 # v8.3.2
```

The pins were verified during planning from the publishers' current upstream release and commit records. They must not be silently replaced. If any pin no longer resolves, implementation or verification stops and the failure is reported for review.

No Docker setup or build action is used. The hosted runner's Docker Compose installation executes the repository's real `docker compose build` path directly.

## Python, uv, and dependency cache

`Application checks` installs exact CPython `3.13.14` and uv `0.11.29`. These match the approved application and Docker toolchain patch versions.

The uv setup action is configured with:

```yaml
version: "0.11.29"
enable-cache: true
cache-dependency-glob: app/uv.lock
working-directory: app
```

Only uv's download cache is persisted, with invalidation tied to `app/uv.lock`. CI never caches `.venv`; `uv sync --locked --all-groups` recreates it from the committed lock on each runner. There is no pip cache or separate `actions/cache` use. A cache miss is expected and must not fail the job.

## PostgreSQL 17 service

Only `Application checks` starts a `postgres:17` service container. The host job connects through the loopback-mapped PostgreSQL port, and a `pg_isready` health check must pass before application steps begin. The database configuration is disposable and CI-only. The application remains PostgreSQL-only; SQLite is not a fallback. The `postgres:17` major tag matches the project version but can move between PostgreSQL 17 patch releases.

The container job likewise uses non-sensitive CI-only Compose interpolation. CI does not create or read `.env`, dump the complete environment, or print expanded Compose configuration.

## Application command order

After checkout and tool setup, `Application checks` runs from `app/` in this exact fail-fast order:

1. `uv lock --check`
2. `uv sync --locked --all-groups`
3. `uv run python --version`
4. `uv run python -m django --version`
5. `uv run ruff format --check .`
6. `uv run ruff check .`
7. `uv run python manage.py check`
8. `uv run python manage.py makemigrations --check --dry-run`
9. `uv run python manage.py migrate --noinput`
10. `uv run pytest`
11. `uv run python manage.py spectacular --validate --file "$RUNNER_TEMP/task-005-schema.yml"`

Lock and static checks fail before the more expensive database and test work. Migration drift is checked before applying committed migrations to the disposable PostgreSQL database. The full test suite uses its own PostgreSQL test database.

Schema validation writes outside the checkout and installs an exit trap before running:

```bash
schema_file="$RUNNER_TEMP/task-005-schema.yml"
trap 'rm -f "$schema_file"' EXIT
uv run python manage.py spectacular --validate --file "$schema_file"
```

The trap removes the one known temporary file whether validation succeeds or fails, so CI does not leave a generated workspace file or require an ignore rule.

## Container command order and cache policy

After checkout, `Container build` runs from `app/`:

1. `docker compose config --quiet`
2. `docker compose build --pull`
3. `docker image inspect --format '{{.Config.User}}' aws-django-ecs-platform-app:local`, with an exact equality assertion against `10001:10001`

Quiet Compose validation checks interpolation and service structure without revealing the resolved values. The build follows the repository's Compose and Dockerfile path and fails on invalid configuration, invalid Dockerfile instructions, unresolved immutable bases, or a lock mismatch in the image build. The image metadata assertion preserves the non-root runtime contract.

The job does not start the stack, push an image, publish an artifact, or use AWS. There is no cross-run Docker cache in TASK-005. The Dockerfile's BuildKit cache mount can help within a builder, but a fresh hosted runner is expected to perform a cold build. Cross-run `type=gha` caching can be considered later only after measuring hosted build duration and re-verifying any required Docker actions.

## Job independence and verified failure behavior

Neither job declares `needs`, so both begin independently. A source-quality or test failure does not hide the container result, and a container failure does not hide application evidence. Branch protection must require both stable checks.

The single implementation pull request confirmed these representative failures:

| Temporary defect | Failed check | Failing step |
| --- | --- | --- |
| Ruff formatting defect | `Application checks` | `Check formatting` |
| Lint-clean deterministic pytest defect | `Application checks` | `Run tests` |
| Invalid Compose configuration | `Container build` | `Validate Compose configuration` |

## One-branch, one-pull-request failure demonstration

TASK-005 used only `feature/task-005-github-actions-ci` and its single implementation pull request. No probe branch or second pull request was created.

Valid content first passed both permanent checks on the pull-request merge ref. The authorized temporary failures were then demonstrated sequentially on that same branch and pull request:

1. a minimal Ruff formatting defect failed `Application checks` at `Check formatting`;
2. a lint-clean deterministic pytest defect failed `Application checks` at `Run tests`;
3. an invalid Compose configuration failed `Container build` at `Validate Compose configuration`.

Each expected failure was observed before valid content was restored. No failing revision was retained in the final branch.

## Temporary history cleanup

After all failure evidence and restorations were observed, the temporary failure and restoration commits were removed from the unmerged feature branch with:

```text
git rebase -i main
```

The cleaned branch was pushed with:

```text
git push --force-with-lease
```

`--force-with-lease` is mandatory because it refuses to overwrite the remote branch when its current tip no longer matches the locally expected remote-tracking state. Plain `--force` lacks that protection and is prohibited. If the lease fails, stop, fetch, inspect the remote change, and request direction rather than overriding it.

History rewriting was limited to the unmerged TASK-005 feature branch; `main` was not rewritten. The final feature history contains only:

```text
docs: define GitHub Actions CI task
ci: add GitHub Actions validation workflow
docs: document GitHub Actions CI
```

Both permanent CI checks passed again after the cleaned branch was pushed. The pull request remains subject to the documented **Create a merge commit** policy; it must not be squash-merged or rebase-merged.

## Branch protection and repository merge settings

The `main` ruleset is active and confirms:

- require a pull request before merging;
- require `Application checks`;
- require `Container build`;
- require conversation resolution;
- require branches to be up to date before merging;
- block force pushes;
- block branch deletion;
- do not require linear history.

Repository merge settings enable merge commits and disable squash merging and rebase merging. TASK-005 therefore retains the **Create a merge commit** policy.

## GitHub verification and completion evidence

The completion gate is satisfied:

- the valid pull-request merge-ref run passed `Application checks`;
- the valid pull-request merge-ref run passed `Container build`;
- a Ruff formatting defect failed `Application checks` at `Check formatting`;
- a lint-clean deterministic pytest defect failed `Application checks` at `Run tests`;
- an invalid Compose configuration failed `Container build` at `Validate Compose configuration`;
- valid content was restored after every failure;
- all temporary failure and restoration commits were removed with `git rebase -i main`;
- the cleaned branch was pushed with `git push --force-with-lease`;
- final feature history contains only the three meaningful commits recorded above;
- the cleaned branch ran and passed both permanent jobs again;
- the active `main` ruleset requires pull requests, both stable checks, conversation resolution, and up-to-date branches;
- the ruleset blocks deletion and force pushes of `main` and does not require linear history;
- merge commits are enabled, while squash and rebase merging are disabled.

## Future CI/CD policy

TASK-005 implements CI only:

- feature branches: local checks and no deployment;
- pull requests to `main`: application CI and container build only;
- pushes to `main`: final CI now, with future image publication and optional staging deployment added by a later approved task;
- production: a reviewed version tag, GitHub Release, or manual dispatch through a protected `production` environment, with approval and deployment of the exact previously tested image digest.

Future AWS authentication must use GitHub OIDC rather than stored long-lived credentials. None of that delivery scope is implemented here.

## Local validation

The approved implementation-phase validation is run from `app/` with the same disposable CI-only settings where applicable:

```text
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

Implementation-phase validation completed successfully on 2026-07-18:

- `uv lock --check` resolved the existing 30-package lock without changing it;
- `uv sync --locked --all-groups` checked the existing 29 installed packages without changing the lock;
- the effective versions were Python 3.13.14 and Django 5.2.16;
- Ruff reported all 52 files formatted and no lint violations;
- Django reported no system-check issues and no migration drift;
- all committed migrations applied successfully to a disposable PostgreSQL 17 container using the CI-only values;
- pytest collected 76 tests and all 76 passed in 155.01 seconds;
- OpenAPI schema validation succeeded and `.tmp-task-005-schema.yml` was removed;
- `docker compose config --quiet` succeeded with the CI-only interpolation values;
- `docker compose build --pull` built `aws-django-ecs-platform-app:local` successfully;
- image inspection returned the exact runtime user `10001:10001`.

The disposable PostgreSQL container used no named volume and was stopped with automatic removal after validation. No local test data remains, and the project's `postgres_data` named volume was not used or modified. The full application stack was not started and no destructive Compose command was run.

## Risks and limitations

- `ubuntu-latest` and the `postgres:17` tag are moving environments; exact Python, uv, action commits, and Dockerfile bases reduce but do not eliminate upstream variation.
- Each hosted container job begins without a cross-run Docker cache; cold-build duration must be observed before a later optimization is justified.
- A manual dispatch on `main` shares concurrency with a `main` push and may cancel or be cancelled by it.
- Feature-branch pushes without an open pull request rely on documented local validation.
- Runtime startup, operational health, Swagger behavior, and persistence remain manual Compose checks; TASK-005's container job intentionally does not start the stack.

## Out of scope

No application, test, migration, settings, dependency, lockfile, Dockerfile, Compose, environment-example, roadmap, AWS, OIDC/IAM, ECR, ECS, Terraform, deployment, production environment, release/tag, Dependabot, CodeQL, package publication, branch-rule automation, or third-party CI change is part of this implementation phase.
