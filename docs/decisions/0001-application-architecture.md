# ADR 0001: Application Architecture

## Status

Accepted

## Context

The system needs a REST API for users, projects, project memberships, and tasks. It requires authenticated access, relational persistence, database migrations, containerized execution, an AWS-compatible deployment target, and maintainable infrastructure and delivery automation.

## Decision

The implemented application uses Django and Django REST Framework for the API, PostgreSQL for relational persistence, Django Admin for administrative operations, and JWT authentication for API access. The repository uses a monorepo layout and Docker containerization.

AWS ECS Fargate is the intended runtime. Terraform is planned for infrastructure management. GitHub Actions is implemented for continuous integration and is planned to support delivery automation. GitHub OIDC is planned for AWS authentication.

Terraform-managed infrastructure, ECR image publication, ECS deployment, AWS OIDC integration, and AWS resources are not implemented.

## Consequences

Django provides a mature model, migration, authentication, and administration foundation. PostgreSQL supports the relational domain and gives application validation a database environment that matches the supported runtime. Docker provides a consistent executable unit for local operation and future deployment.

The monorepo keeps application, container, and future infrastructure changes together, which simplifies coordinated interface changes. It also requires clear boundaries so infrastructure additions do not obscure application behavior.

ECS Fargate avoids cluster-node management while retaining a standard container runtime. Terraform and GitHub Actions introduce declarative infrastructure and automated delivery concerns that must be maintained as the AWS implementation is added.

## Alternatives considered

Kubernetes would provide broader orchestration features but adds operational complexity beyond the current container runtime requirements.

Separate application and infrastructure repositories would provide stronger repository isolation but would require coordination across independently versioned changes.

Serverless functions would reduce server management for individual endpoints but do not align as directly with the long-running Django application and relational migration model.

A non-Django web framework could support the API but would require separate choices for administration, migrations, and other application foundations already provided by Django.
