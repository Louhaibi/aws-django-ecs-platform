# ADR 0001: Project Foundation

- Status: Accepted
- Date: 2026-07-16

## Context

The project must strengthen a cloud, platform, and DevOps engineering portfolio while providing a realistic application workload. Infrastructure, delivery, security, observability, and operational reasoning are the primary learning goals.

## Decision

Use Python with Django and Django REST Framework, PostgreSQL, Django Admin plus REST API, JWT authentication, a task-management domain, a monorepo, Docker, Terraform, ECS Fargate, GitHub Actions, progressive dev/staging/prod environments, separate environment directories and state rather than Terraform workspaces, and GitHub OIDC.

An existing open-source Django/Docker foundation may be studied or adapted, but the task-management domain will be developed incrementally and clearly attributed.

## Rationale

Django supplies authentication, administration, migrations, database models, and a mature ecosystem. ECS Fargate demonstrates containers, networking, load balancing, IAM, logging, scaling, and deployment without adding Kubernetes complexity too early.

A monorepo keeps application and infrastructure evolution visible in one place and makes the initial Codex workflow easier to control.

## Consequences

Positive: clear recruiter-facing project, strong AWS/Terraform alignment, visible incremental development, manageable application complexity, and room for later module extraction.

Trade-offs: less repository independence, less isolation than an enterprise multi-account design, no Kubernetes demonstration yet, and some repeated environment configuration.

## Deferred decisions

The exact upstream reference, dependency-management tool, settings layout, OpenAPI package, JWT package, and container build details will be selected in dedicated tasks.
