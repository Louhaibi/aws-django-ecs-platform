# AWS Django ECS Platform

A production-oriented cloud and platform engineering portfolio project built around a Django task-management API.

## Objective

Demonstrate how to take a backend application from local development to a secure, repeatable, observable, and cost-aware AWS deployment.

The main engineering focus is AWS architecture, Terraform, Docker, ECS Fargate, PostgreSQL and RDS, GitHub Actions, security, secrets management, monitoring, operations, and multi-environment delivery.

## Planned application

The initial backend will provide Django Admin, a REST API, JWT authentication, projects and project membership, tasks and assignment, status, priority, due dates, owner/member access controls, and health/readiness endpoints.

A custom frontend is intentionally excluded from the first release.

## Delivery approach

1. Establish the Django foundation.
2. Implement and test the task-management domain.
3. Containerize the application.
4. Deploy a low-cost dev environment on AWS.
5. Add CI/CD, security scanning, and observability.
6. Introduce staging.
7. Introduce a temporary production-demonstration environment.

The repository is currently in the project-foundation phase. No AWS application infrastructure has been deployed yet.

See `docs/project-charter.md`, `docs/decisions/0001-project-foundation.md`, and `docs/tasks/TASK-001-project-bootstrap.md`.
