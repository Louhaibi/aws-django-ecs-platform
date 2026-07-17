# TASK-003: Implement Authenticated REST API, JWT, Permissions, and OpenAPI

## Status

Complete.

## Objective

Expose the existing users, projects, project memberships, and tasks domain through a versioned REST API.

The API must provide JWT authentication, strict queryset isolation, object-level authorization, filtering, consistent validation errors, and interactive OpenAPI documentation.

The implementation must preserve the domain rules established in TASK-002 and must not weaken model validation or database constraints.

## Required technologies

Plan and implement using:

- Django REST Framework;
- Simple JWT for access and refresh tokens;
- drf-spectacular for OpenAPI schema generation and interactive API documentation;
- django-filter only if the plan demonstrates that it is the clearest supported filtering approach.

Before implementation, verify compatible current package versions against authoritative package documentation or the package index available to `uv`.

The exact resolved versions must be committed in `app/uv.lock`.

## API versioning and routes

Use a stable versioned prefix:

```text
/api/v1/
```

Required authentication and documentation routes:

```text
/api/v1/auth/token/
/api/v1/auth/token/refresh/
/api/v1/auth/token/verify/
/api/v1/users/me/
/api/schema/
/api/docs/
```

The planning phase must propose exact resource routes for:

- projects;
- project memberships;
- tasks.

Prefer clear conventional REST routes. Avoid adding a routing dependency solely for nested URLs unless the plan demonstrates a concrete benefit.

## Authentication

Implement JWT authentication.

Requirements:

- unauthenticated access to protected API endpoints returns the appropriate authentication error;
- token obtain accepts the existing Django username and password credentials;
- token refresh and token verification are supported;
- public user registration is not implemented;
- password reset and email verification are not implemented;
- Django Admin session authentication continues to work independently;
- API documentation must explain how to authenticate with a bearer token.

Do not place sensitive personal information or unnecessary claims inside JWT payloads.

## Current-user endpoint

Implement a read-only endpoint for the authenticated user:

```text
GET /api/v1/users/me/
```

It may return only the approved safe fields:

- id;
- username;
- email;
- first_name;
- last_name.

Do not expose:

- password data;
- permission collections;
- staff or superuser management;
- a general user directory;
- other users' private information.

## Project API

Authenticated users may create projects.

Creation rules:

- the authenticated user becomes the project owner;
- clients must not set or override `owner`;
- owner information is read-only in API representations.

Visibility rules:

- users may list and retrieve only projects they own or projects in which they have a membership;
- unrelated projects must not appear in list results;
- direct retrieval of an unrelated project must not reveal its existence.

Modification rules:

- only the project owner may update or delete the project;
- project ownership cannot be changed through the API;
- the immutable-owner domain rule remains enforced by the model.

The planning phase must decide whether `PUT` is supported or whether updates are deliberately limited to `PATCH`, and explain the choice.

## Project membership API

Visibility rules:

- only users who can access a project may view its memberships;
- membership responses may expose only safe user identity fields needed by the application.

Modification rules:

- only the project owner may create, update, or delete memberships;
- an owner cannot be added as a membership;
- duplicate memberships remain invalid;
- valid roles remain `member` and `manager`;
- clients cannot move an existing membership to another project or another user through update operations;
- ownership transfer is not implemented.

The plan must define whether memberships use nested project routes or conventional flat routes with project filtering.

Membership deletion keeps the historical TASK-002 behavior:

- existing tasks retain creator and assignee references;
- no automatic reassignment or historical rewrite occurs.

## Task API

Visibility rules:

- users may list and retrieve only tasks belonging to accessible projects;
- unrelated tasks must not appear in list results;
- direct retrieval must not reveal inaccessible tasks.

Creation rules:

- only project owners and project managers may create tasks through this API;
- `creator` is always the authenticated user and is read-only to clients;
- the selected project must be accessible;
- the assignee must be the project owner or a current project member;
- tasks may be unassigned;
- due dates remain optional.

Modification rules:

- project owners and project managers may update tasks;
- project members have read-only task access in TASK-003;
- only the project owner may delete tasks;
- clients cannot change `creator`;
- clients cannot move a task to another project after creation;
- model validation remains authoritative for creator and assignee eligibility.

Manager and member authorization differences begin in this task:

- owner: full project visibility, project management, membership management, task creation/update/delete;
- manager: project and membership read access, task creation and update, but no task deletion and no membership or project management;
- member: read-only project, membership, and task access.

These are API authorization rules. They do not change the persisted membership roles or TASK-002 model constraints.

## Queryset isolation and authorization

Security must be enforced in both places:

1. queryset filtering so list endpoints never include inaccessible objects;
2. object-level permission checks for retrieve, update, and delete operations.

Do not rely on object-level permissions alone for lists.

The plan must describe reusable queryset and permission components without introducing an unnecessarily complex policy framework.

Unauthorized and inaccessible object behavior must be tested carefully to avoid cross-project data leakage.

## Serialization and validation

Serializers must:

- distinguish writable and read-only fields explicitly;
- prevent clients from setting owner and creator;
- prevent project reassignment after creation where required;
- preserve TASK-002 model `ValidationError` behavior;
- translate domain validation errors into clear API `400 Bad Request` responses;
- avoid leaking stack traces or internal database details;
- provide useful nested summary data only when it does not create excessive queries or duplicated write paths.

The plan must explain how Django model validation errors raised from `save() -> full_clean()` will be converted into DRF validation responses.

Do not duplicate every domain rule in serializers unless needed for API-specific usability or field-level error presentation.

## Filtering, search, ordering, and pagination

Project listing should support a small useful set of options, such as search by name.

Task listing must support filtering by:

- project;
- status;
- priority;
- assignee;
- due date where practical.

Task listing should support:

- search by title and description;
- deterministic ordering;
- ordering by the selected safe fields title, created_at, updated_at, and due_date.

Membership listing should support filtering by project and role.

Use pagination globally for collection endpoints.

The plan must propose:

- pagination style and default page size;
- exact filter fields;
- exact search fields;
- exact ordering fields;
- any database-query optimizations using `select_related()` or `prefetch_related()`.

## API response behavior

Use conventional HTTP status codes:

- `200` for successful reads and updates;
- `201` for successful creates;
- `204` for successful deletes;
- `400` for validation errors;
- `401` for missing or invalid authentication;
- `403` for authenticated users lacking permission where revealing object existence is acceptable;
- `404` for objects excluded by access-scoped querysets.

Do not create a custom response envelope in TASK-003.

Use DRF's standard error structure unless a narrowly scoped exception handler is required to translate model validation errors consistently.

## OpenAPI and manual visualization

Generate an OpenAPI schema and interactive Swagger UI using drf-spectacular.

Required routes:

```text
/api/schema/
/api/docs/
```

The documentation must:

- show JWT bearer authentication;
- describe important create and update fields;
- distinguish read-only fields;
- include the main expected error responses where practical;
- not expose secrets or real credentials.

Manual verification must allow the developer to:

1. start PostgreSQL and Django;
2. create or reuse test users;
3. obtain a JWT token;
4. authorize Swagger UI;
5. create a project;
6. add a manager and a member;
7. create and update a task as an owner or manager;
8. verify that a member has read-only access;
9. verify that an unrelated user cannot see the project or tasks;
10. refresh and verify a JWT;
11. stop services safely.

The interactive documentation is the primary visual interface for TASK-003.

## Tests

Add focused PostgreSQL-backed API tests covering at least:

### Authentication

- valid token obtain;
- invalid credentials;
- refresh;
- verify;
- protected endpoint without authentication;
- current-user endpoint.

### Projects

- authenticated project creation assigns request user as owner;
- owner cannot be supplied or changed by the client;
- accessible project listing;
- unrelated project isolation;
- owner update/delete;
- manager/member cannot update or delete the project.

### Memberships

- accessible membership listing;
- unrelated membership isolation;
- owner create/update/delete;
- manager/member cannot manage memberships;
- owner membership rejection;
- duplicate membership rejection;
- immutable project and user relationships on update.

### Tasks

- owner and manager creation;
- member creation rejection;
- creator automatically uses request user;
- creator cannot be changed;
- project cannot be moved after creation;
- valid owner/member/manager assignee;
- unrelated assignee rejection;
- optional assignee and due date;
- owner and manager update;
- member update rejection;
- owner delete;
- manager/member delete rejection;
- accessible listing and filtering;
- unrelated task isolation;
- historical former-member behavior returns a controlled validation response rather than a server error.

### Schema

- schema endpoint responds successfully;
- documentation endpoint responds successfully;
- schema includes JWT security and the primary routes.

Prefer maintainable fixtures and helper functions. Do not add a third-party factory package unless explicitly approved.

## Documentation

Update:

- `README.md`;
- `CONTRIBUTING.md` only if required commands or development workflow change;
- `docs/tasks/TASK-003-rest-api-jwt-openapi.md`.

Create a new ADR only if the planning phase identifies a durable architectural decision that cannot be adequately recorded in the task document.

Do not create an ADR merely to list API routes or serializer fields.

The final TASK-003 document must record:

- final routes;
- authorization matrix;
- queryset isolation strategy;
- serializer write/read boundaries;
- authentication configuration;
- pagination and filters;
- OpenAPI routes;
- automated checks;
- manual Swagger verification;
- known limitations.

## Explicitly out of scope

Do not implement:

- public user registration;
- password reset;
- email verification;
- social login;
- browser frontend;
- React, Vue, or other frontend frameworks;
- cookies or browser session authentication for the API;
- token blacklisting or logout endpoints unless the approved plan demonstrates a current requirement;
- ownership transfer;
- project invitations;
- comments;
- attachments;
- labels or tags;
- subtasks;
- activity history;
- notifications;
- Celery;
- Redis;
- WebSockets;
- rate limiting beyond documenting it as future work;
- Django application containerization;
- AWS;
- Terraform;
- GitHub Actions.

## Planning questions Codex must answer

Before editing, explain:

1. exact dependencies and compatible version constraints;
2. exact route design;
3. ViewSets, generic views, or another DRF structure and why;
4. queryset isolation strategy for each resource;
5. permission classes and authorization matrix;
6. serializer fields and read/write boundaries;
7. handling of model `ValidationError`;
8. project and creator immutability through the API;
9. membership relationship immutability;
10. pagination, filtering, search, and ordering;
11. query optimization;
12. JWT settings and token lifetimes;
13. OpenAPI integration;
14. exact test organization;
15. expected file tree;
16. validation commands;
17. manual Swagger verification;
18. documentation changes;
19. security risks and known limitations.

For each important choice:

- explain why it is suitable;
- mention a reasonable alternative;
- distinguish list-query isolation from object permission checks;
- avoid prematurely implementing future infrastructure or frontend concerns.

Use authoritative current documentation for version-sensitive behavior.

## Acceptance criteria

- JWT token obtain, refresh, and verify work.
- Authenticated users can access `GET /api/v1/users/me/`.
- Projects, memberships, and tasks are exposed through versioned endpoints.
- Lists and direct retrievals do not leak inaccessible objects.
- Authorization matches the approved owner, manager, and member matrix.
- Owner and creator cannot be client-controlled contrary to domain rules.
- Domain validation becomes controlled API validation responses.
- Filtering, search, ordering, and pagination work as approved.
- OpenAPI schema and Swagger UI work.
- Automated tests pass against PostgreSQL.
- Manual Swagger verification steps are documented.
- No unrelated features or infrastructure are introduced.
- No secrets or local data are committed.
- No commit or push occurs until review.

## Suggested commit message

```text
feat: add authenticated task management API
```

## Implementation record

### Dependencies

TASK-003 adds these direct runtime constraints, locked exactly in `app/uv.lock`:

- `djangorestframework>=3.17.1,<3.18` (resolved 3.17.1);
- `djangorestframework-simplejwt>=5.5.1,<5.6` (resolved 5.5.1);
- `drf-spectacular>=0.30.0,<0.31` (resolved 0.30.0);
- `django-filter>=26.1,<26.2` (resolved 26.1).

### Routes and HTTP methods

```text
POST /api/v1/auth/token/
POST /api/v1/auth/token/refresh/
POST /api/v1/auth/token/verify/
GET  /api/v1/users/me/
GET, POST /api/v1/projects/
GET, PATCH, DELETE /api/v1/projects/{id}/
GET, POST /api/v1/memberships/
GET, PATCH, DELETE /api/v1/memberships/{id}/
GET, POST /api/v1/tasks/
GET, PATCH, DELETE /api/v1/tasks/{id}/
GET /api/schema/
GET /api/docs/
```

Resource updates are PATCH-only; PUT returns 405. Memberships use flat routes and `?project=<id>` filtering. No API root or nested-router dependency is introduced.

### Authentication and public routes

Application endpoints use only Simple JWT bearer authentication and `IsAuthenticated`. Access tokens last 15 minutes and refresh tokens one day; refresh rotation, blacklisting, and last-login updates are disabled. JWTs use HS256 with required `JWT_SIGNING_KEY`, which must be non-empty and is distinct from Django's `SECRET_KEY`. The local example value is deliberately unsafe. Production must provide the signing key through secret management; asymmetric signing and key rotation are deferred.

Token obtain/refresh/verify, schema, and Swagger use explicit empty authentication classes plus `AllowAny`. They are documented as public in the generated schema. `/api/v1/users/me/` and every project, membership, and task operation are documented as JWT bearer protected. Swagger does not persist authorization in browser storage.

### Serialization and authorization

`/users/me/` exposes only ID, username, email, first name, and last name. Resource summaries expose only safe user identity fields and omit member email addresses. Owner and creator are server-controlled. Task project, membership project, and membership user are create-only; immutable input on an update returns 400 rather than being silently ignored.

| Action | Owner | Manager | Member | Unrelated user |
| --- | --- | --- | --- | --- |
| Project read | Allow | Allow | Allow | Excluded / 404 |
| Project patch/delete | Allow | 403 | 403 | 404 |
| Membership read | Allow | Allow | Allow | Excluded / 404 |
| Membership create/patch/delete | Allow | 403 | 403 | Inaccessible project not disclosed |
| Task read | Allow | Allow | Allow | Excluded / 404 |
| Task create/patch | Allow | Allow | 403 | Inaccessible project not disclosed |
| Task delete | Allow | 403 | 403 | 404 |

`get_queryset()` access-scopes projects to owner/member rows, and memberships/tasks to those accessible projects. This protects lists and causes inaccessible detail lookups to return 404. Object permissions remain a second control for visible-object mutations. Create permissions are checked against the validated project because DRF does not apply object permissions during creation.

Domain `ValidationError` raised by `save() -> full_clean()` is converted to DRF field or `non_field_errors` 400 responses. Duplicate membership is checked normally in the serializer. Its unique-constraint race fallback inserts inside an inner `transaction.atomic()` savepoint, catches `IntegrityError` only after that block exits, then returns a duplicate 400 only if the exact project/user row exists. Unrelated integrity errors are re-raised without database text in a response.

### Collections and performance

All collections use page-number pagination (20 default, client `page_size` up to 100). Projects support name search and safe ordering. Memberships filter by `project` and `role`. Tasks filter by project, status, priority, assignee, exact/range due date, and unassigned state; they search title/description and order by title, due date, created date, or updated date. Ordering appends ID as a deterministic tie-breaker. Priority is filterable but intentionally not sortable because stored text order is not business-priority order.

Project querysets select owners; membership querysets select project, project owner, and user; task querysets select project, project owner, creator, and assignee. No new index is added before measured workload justifies one.

### OpenAPI, tests, and manual verification

drf-spectacular serves `/api/schema/` and `/api/docs/`; request/response components are split so read-only fields are visible in the schema. The automated suite covers token flows, public/protected routes, current-user boundaries, resource authorization, list isolation, immutable relationships, validation conversion, duplicate savepoint handling, filters, search, ordering, schema security, and Swagger availability.

Final automated validation completed with Python 3.13.14, Django 5.2.16, and PostgreSQL 17: all 33 API tests passed and the complete project suite passed with 73 tests. Ruff formatting and lint checks passed, Django system checks passed, the migration drift check reported no new migrations, and `spectacular --validate` schema generation passed.

Manual Swagger verification completed successfully. Swagger UI loaded at `/api/docs/`; unauthenticated `GET /api/v1/users/me/` returned 401; token obtain returned 200; and authenticated `GET /api/v1/users/me/` returned 200 with only the approved fields. Project creation returned 201 with the authenticated user assigned automatically as owner. Project listing returned 200 with pagination, retrieval returned 200, and PATCH returned 200. Attempts to change the project owner returned 400. TASK-003 is complete.

### Limitations

No registration, password reset, social login, cookie API authentication, invitations, ownership transfer, logout, blacklist, refresh rotation, rate limiting, frontend, background jobs, containerization, AWS, Terraform, or CI/CD is included. Bearer tokens require HTTPS outside local development. Cross-row membership validation has unavoidable concurrency limits beyond the exact duplicate savepoint case, and historical former-member task references remain intentionally subject to current-access validation on later ordinary saves.
