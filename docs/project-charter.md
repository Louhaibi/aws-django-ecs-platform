# Project Charter

## Mission

Build a production-oriented, multi-environment platform for a Django task-management API while developing deep practical knowledge of AWS, Terraform, DevOps, and platform engineering.

The result must be understandable to recruiters and technical interviewers, reproducible from source code, and developed through a clear incremental Git history.

## Target roles

Primary: Cloud Engineer and Platform Engineer.

Secondary: DevOps Engineer and Cloud Infrastructure Engineer.

Reliability engineering practices will be included without presenting the project as a full SRE platform.

## Application scope

Initial capabilities:

- users managed through Django Admin;
- JWT authentication for REST clients;
- projects owned by users;
- project membership;
- tasks belonging to projects;
- task assignment to project members;
- task status, priority, description, and due date;
- filtering by relevant task fields;
- access restricted to project owners and members;
- health and readiness endpoints;
- generated API documentation.

No custom frontend is included initially.

## Technology baseline

Application: Python, Django, Django REST Framework, PostgreSQL, pytest, and Gunicorn for deployed environments.

Delivery and infrastructure: Docker, Terraform, AWS ECS Fargate, ECR, Application Load Balancer, RDS PostgreSQL, Secrets Manager, CloudWatch, GitHub Actions, GitHub OIDC, TFLint, Checkov, and Trivy.

## Repository strategy

Use a monorepo for the first complete platform. Application code, infrastructure code, workflows, scripts, and documentation remain together. Reusable Terraform modules may later be extracted into a separate repository.

## Environment strategy

Local: Django, PostgreSQL through Docker, tests, and application development.

Dev: first AWS environment, low-cost settings, and automatic application deployment after the workflow is mature.

Staging: separate state and resources, production-like validation, and manual deployment.

Prod: separate state and resources, manual deployment with approval, temporary production-demonstration mode, and stronger availability, backups, monitoring, and protection.

All environment configurations may exist in Git without all environments running simultaneously.

A mature enterprise design would normally use separate AWS accounts. This portfolio initially uses one account with logical separation because AWS Organizations conflicts with the current Free Plan and budget strategy.

## Cost strategy

Normal monthly target: approximately EUR 20 or less.

- destroy resources when not needed;
- prefer low-cost dev settings;
- avoid leaving expensive networking and database resources running;
- support a temporary production-demonstration configuration;
- document expected costs;
- use AWS budgets and billing alerts;
- make cleanup explicit and repeatable.

## Delivery rules

Application delivery: dev automatic after approval; staging manual; prod manual with approval.

Infrastructure delivery: pull requests run formatting, validation, linting, security scans, and Terraform plans. Apply always requires explicit approval.

## Security principles

No credentials in source control. GitHub Actions uses OIDC. RDS and ECS tasks are private. Public traffic enters through the load balancer. Secrets remain outside source code. Containers run as non-root. Dependencies and images are scanned.

## Non-goals for the first release

Custom frontend, public registration, social login, background workers, Celery, Redis, email, WebSockets, Kubernetes, microservices, multi-region deployment, complex organization-wide RBAC, and AWS multi-account architecture.

## Development method

Understand the concept, define a bounded task, let Codex inspect and propose a plan, review it, authorize implementation, run checks, review the diff, commit reviewed work, update documentation, and select the next task.

Codex must not implement the entire roadmap in one change.
