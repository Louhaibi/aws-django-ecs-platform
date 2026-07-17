# TASK-002: Implement Task-Management Domain Models and Django Admin

## Status

Complete.

## Objective

Implement the core task-management data model and provide a usable Django
Admin interface for manually creating and inspecting projects, memberships,
and tasks.

This task establishes the domain foundation that future REST API and
permission tasks will use.

## Scope

TASK-002 creates two Django applications under `app/apps/`:

- `projects`, containing `Project` and `ProjectMembership`;
- `tasks`, containing `Task`.

It includes model relationships, database constraints, domain validation,
Django Admin registrations, initial migrations, PostgreSQL-backed tests, and
current-state documentation.

## Exclusions

This task does not add Django REST Framework, JWT, serializers, API views,
routes, OpenAPI, a frontend, ownership transfer, permission enforcement,
signals, a domain service, automatic reassignment, Celery, Redis, email,
comments, labels, attachments, subtasks, notifications, Django
containerization, AWS, Terraform, or GitHub Actions.

The `member` and `manager` roles both provide project access in this task.
Differences in their future permissions are deferred.

## Final model design

All models use the implicit `BigAutoField` primary key configured by
`DEFAULT_AUTO_FIELD`.

### Project

| Field | Definition |
| --- | --- |
| `id` | Implicit `BigAutoField(primary_key=True)` |
| `name` | `CharField(max_length=255)` |
| `description` | `TextField(blank=True)` |
| `owner` | Required user foreign key, `PROTECT`, related name `owned_projects` |
| `created_at` | `DateTimeField(auto_now_add=True)` |
| `updated_at` | `DateTimeField(auto_now=True)` |

Project names are not unique. `description` uses an empty string rather than
database `NULL` when omitted.

`Project.owner` is required at creation and immutable afterward. Model
validation fetches the persisted `owner_id` for an existing row and rejects a
different proposed value with a field-specific `ValidationError`. Ownership
transfer requires a future transactional workflow and is not implemented.

`Project.is_accessible_by(user)` returns `False` for `None`, anonymous users,
and users without a persisted primary key. It returns `True` immediately when
`user.pk == owner_id`; otherwise, for a persisted project, it checks for a
membership using `user_id` without loading a membership object.

The string representation is the project name.

### ProjectMembership

| Field | Definition |
| --- | --- |
| `id` | Implicit `BigAutoField(primary_key=True)` |
| `project` | Required `Project` foreign key, `CASCADE`, related name `memberships` |
| `user` | Required user foreign key, `CASCADE`, related name `project_memberships` |
| `role` | `CharField(max_length=20)`, `Role` choices, default `member` |
| `created_at` | `DateTimeField(auto_now_add=True)` |

Membership roles are:

- `member` / `Member`;
- `manager` / `Manager`.

The owner is not represented by a membership row and has access automatically.
Adding the owner as a member or manager is rejected by model validation.

The string representation includes user, project, and displayed role.

### Task

| Field | Definition |
| --- | --- |
| `id` | Implicit `BigAutoField(primary_key=True)` |
| `project` | Required `Project` foreign key, `CASCADE`, related name `tasks` |
| `title` | `CharField(max_length=255)` |
| `description` | `TextField(blank=True)` |
| `status` | `CharField(max_length=20)`, `Status` choices, default `todo` |
| `priority` | `CharField(max_length=10)`, `Priority` choices, default `medium` |
| `assignee` | Optional user foreign key, `SET_NULL`, related name `assigned_tasks` |
| `due_date` | Optional `DateField` |
| `creator` | Required user foreign key, `PROTECT`, related name `created_tasks` |
| `created_at` | `DateTimeField(auto_now_add=True)` |
| `updated_at` | `DateTimeField(auto_now=True)` |

Task statuses are:

- `todo` / `To do`;
- `in_progress` / `In progress`;
- `done` / `Done`;
- `cancelled` / `Cancelled`.

Task priorities are:

- `low` / `Low`;
- `medium` / `Medium`;
- `high` / `High`;
- `urgent` / `Urgent`.

`Task.creator` is required at creation and immutable afterward. Model
validation compares the persisted and proposed `creator_id` values and rejects
a change. Django Admin does not infer the creator from the logged-in user.

A task creator and any non-null assignee must currently be the project owner
or have a project membership whenever an ordinary task save is attempted. An
unassigned task and a task without a due date are valid. Past due dates are not
prohibited by this task.

The string representation includes the task title and project.

## Ownership, membership, and historical tasks

Project access is defined as owner or membership. The owner does not need and
cannot have a redundant membership row.

Deleting a `ProjectMembership` does not delete, unassign, reassign, or modify
existing tasks. Historical `creator_id` and `assignee_id` references remain
unchanged. No membership-deletion signal or blocker is used.

Current access is re-evaluated when a task is later saved normally:

- a former-member assignee must be cleared or replaced with an eligible user;
- a former-member creator cannot be changed, so access must be restored before
  the task can be saved again.

This behavior is intentional for TASK-002.

## Database guarantees

The initial migrations create these named constraints:

| Name | Guarantee |
| --- | --- |
| `projects_projectmembership_unique_project_user` | One membership per project/user pair |
| `projects_projectmembership_valid_role` | Role is `member` or `manager` |
| `tasks_task_valid_status` | Status is one of the four supported values |
| `tasks_task_valid_priority` | Priority is one of the four supported values |

Primary keys, required-column nullability, foreign keys, and PostgreSQL field
lengths provide their normal database guarantees. The membership unique
constraint remains authoritative during concurrent writes.

Owner immutability, creator immutability, owner-membership exclusion, and the
owner-or-member task access rule require cross-row or historical comparisons.
They are application-level validation and are not expressible through the
ordinary check constraints used here.

## Application validation boundary

`Project.save()`, `ProjectMembership.save()`, and `Task.save()` call
`full_clean()` before the normal Django save operation. This makes ordinary
instance saves and `objects.create()` enforce field, model, uniqueness, and
constraint validation outside Django Admin as well as within it.

Admin read-only fields are excluded from generated `ModelForm` fields. When a
historical creator is currently ineligible, model validation therefore reports
the blocking creator error as a non-field Admin form error. Direct model
validation continues to attach it to `creator`. This avoids an Admin server
error without weakening validation.

The following ORM operations bypass model `save()` and therefore bypass the
approved application-validation workflow:

- `bulk_create()`;
- `bulk_update()`;
- `QuerySet.update()`.

They must not be used for these domain models without a separately approved
validation workflow. Database constraints still protect the limited rules
they can express. Tests use `bulk_create()` only inside isolated transactions
to prove database constraint enforcement.

## Django Admin

### Projects

`ProjectAdmin` provides owner and timestamp list columns, newest-first
ordering, owner-aware search, owner autocomplete, related-object query
optimization, and a tabular membership inline.

`owner` is selectable on the add form. `get_readonly_fields()` adds `owner` on
the change form without mutating the class-level read-only collection.
Creation and update timestamps are always read-only.

### Memberships

`ProjectMembershipAdmin` displays project, user, role, and creation time. It
supports role/date filters, project/user search, project/user autocomplete,
newest-first ordering, and related-object query optimization.

### Tasks

`TaskAdmin` displays title, project, status, priority, assignee, creator, due
date, and update time. It supports status, priority, due-date, and creation-date
filters; task/project/user search; project, assignee, and creator autocomplete;
newest-first ordering; and related-object query optimization.

`creator` is selectable on the add form. `get_readonly_fields()` adds
`creator` on the change form without mutating the class-level collection.
Creation and update timestamps are always read-only.

Assignee and creator autocomplete choices are not dynamically filtered by the
selected project. Model validation rejects an ineligible selection on submit.

## Migrations

The implementation includes:

- `projects/migrations/0001_initial.py`;
- `tasks/migrations/0001_initial.py`.

The projects migration depends on the swappable user model. The tasks
migration depends on the projects initial migration and the swappable user
model. Both migrations apply cleanly to PostgreSQL 17.

## Automated tests

Tests are organized under:

```text
app/tests/
|-- conftest.py
|-- projects/
|   |-- test_admin.py
|   `-- test_models.py
|-- tasks/
|   |-- test_admin.py
|   `-- test_models.py
`-- test_smoke.py
```

Coverage includes creation, defaults, ownership, immutable owner and creator,
safe access checks for missing/anonymous/unsaved users, member and manager
access, membership uniqueness, redundant owner membership, database choice
constraints, valid and invalid creators/assignees, unassigned tasks, optional
due dates, historical membership deletion, restored access, deletion behavior,
string representations, Admin registration/configuration, dynamic read-only
fields, and the Admin non-field error fallback.

The final suite contains 40 passing PostgreSQL-backed tests.

## Automated validation

Run from `app/`:

```powershell
uv lock --check
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
uv run python manage.py showmigrations projects tasks --plan
uv run pytest
```

Run from the repository root:

```powershell
git diff --check
git check-ignore app/.env
git status --short
```

Validated versions and results:

- Python 3.13.14;
- Django 5.2.16;
- PostgreSQL Compose service healthy during validation;
- both initial migrations applied;
- no pending model changes;
- Ruff formatting and linting passed;
- Django system checks passed;
- 40 tests passed.

## Manual browser verification

1. From `app/`, start PostgreSQL and apply migrations:

   ```powershell
   docker compose up -d --wait --wait-timeout 60 db
   uv run python manage.py migrate
   ```

2. Create a local administrator if one does not already exist:

   ```powershell
   uv run python manage.py createsuperuser
   ```

3. Start Django:

   ```powershell
   uv run python manage.py runserver
   ```

4. Open `http://127.0.0.1:8000/admin/` and sign in.

5. Create owner, member, and unrelated users.

6. Create a project. Confirm `owner` is selectable on the add form, becomes
   read-only after creation, and no owner membership row is created.

7. Add member and manager memberships through the project inline or standalone
   membership page. Confirm duplicate membership and owner membership are
   rejected, and role filters and search work.

8. Create tasks with owner and member creators/assignees. Confirm unrelated
   users are rejected, while blank assignee and due date are accepted. Confirm
   task search and status/priority filters work.

9. Reopen a task and confirm `creator` is read-only.

10. Create a member-authored and member-assigned task, then delete only the
    membership. Confirm the task retains the same creator and assignee. Attempt
    to save it and confirm current-access validation blocks the save without a
    server error. Restore membership and confirm the task can be saved again.
    For an assignee-only failure, clearing or replacing the assignee permits the
    save.

11. Stop the development server with `Ctrl+C`.

12. Stop PostgreSQL while retaining its named volume:

    ```powershell
    docker compose stop db
    ```

The superuser and manually created records remain in the local PostgreSQL named
volume. They may be deleted through Admin. Do not run
`docker compose down --volumes` unless an intentional database reset is
required.

No API requests or API documentation URL apply because TASK-002 adds no API.

## Known limitations and deferred workflows

- Ownership transfer is not implemented.
- A former-member creator makes a task unsaveable through the approved ordinary
  workflow until project access is restored.
- Membership removal does not automatically clear an assignee.
- Cross-table access validation has a concurrency window and is not a database
  guarantee.
- Bulk ORM writes and raw SQL can bypass application validation.
- Admin autocomplete choices are not dynamically scoped to a project.
- Role-specific authorization, REST serializers, and permission enforcement
  are deferred to later tasks.
- No index beyond primary keys, foreign-key indexes, and constraint-backed
  indexes is added before real query patterns justify one.
