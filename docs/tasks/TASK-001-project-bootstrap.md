# TASK-001: Establish the Django Project Foundation

## Status

Ready for planning. Do not implement until the proposed plan is reviewed.

## Objective

Create the smallest maintainable Django project foundation for future task-management development.

The task establishes the local Python application structure, dependency management, environment-based settings, PostgreSQL configuration, and a basic automated test command.

## Required scope

- select and document a supported Python version;
- select and document a supported Django version;
- select a Python dependency-management approach;
- create the minimal Django project;
- configure settings through environment variables;
- configure PostgreSQL as the development database;
- provide a safe example environment file without real secrets;
- add a basic test framework and one smoke test;
- add formatting and linting foundations appropriate for Python;
- document local setup and validation commands;
- keep the project runnable without implementing business-domain models.

## Explicitly out of scope

Do not add Project, Membership, or Task models; REST endpoints; JWT; Docker; AWS; Terraform; GitHub Actions; Celery; Redis; email; frontend code; Kubernetes; production settings; or a large boilerplate with unrelated features.

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
9. whether an open-source foundation should be adapted and what attribution is required.

Wait for approval after presenting the plan.

## Acceptance criteria

- Django starts with documented local configuration;
- no real secret is committed;
- PostgreSQL configuration comes from environment variables;
- a smoke test passes;
- formatting and linting pass;
- dependencies are pinned or locked reproducibly;
- README describes only implemented capabilities;
- implementation remains limited to the foundation;
- Codex reports files changed and commands executed.

## Suggested commit

```text
chore: establish the Django project foundation
```
