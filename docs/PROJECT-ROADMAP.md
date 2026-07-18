# aws-django-ecs-platform — Project Roadmap

## Current progress

| Task | Title | Status |
|---|---|---|
| TASK-001 | Project bootstrap | Complete |
| TASK-002 | Domain models and Django Admin | Complete |
| TASK-003 | Authenticated REST API, JWT, permissions, filtering, pagination, and OpenAPI | Complete |
| TASK-004 | Django containerization and full local Compose stack | Complete |
| TASK-005 | GitHub Actions CI | Next |
| TASK-006 | Terraform bootstrap and remote state | Planned |
| TASK-007 | AWS network foundation | Planned |
| TASK-008 | ECR repository and image publishing | Planned |
| TASK-009 | RDS PostgreSQL | Planned |
| TASK-010 | ECS Fargate deployment | Planned |
| TASK-011 | Automated ECS deployment pipeline | Planned |
| TASK-012 | Domain and TLS | Planned |
| TASK-013 | Observability and operational safeguards | Planned |
| TASK-014 | Autoscaling and resilience | Planned |
| TASK-015 | Security and production-readiness review | Planned |

---

## TASK-004 — Django containerization and full local Compose stack

**Goal:** Run Django and PostgreSQL together through Docker Compose using a production-oriented application image.

**Main scope**

- Add an application `Dockerfile`
- Add `.dockerignore`
- Run the application as a non-root user
- Add a container startup/entrypoint strategy
- Run migrations safely
- Add an application health endpoint
- Extend `compose.yaml` with the Django service
- Add service health checks and dependencies
- Preserve PostgreSQL data through the named volume
- Keep secrets in ignored environment files
- Document build, start, logs, shell, migrations, tests, and shutdown
- Verify Swagger and API access through the containerized stack

**Out of scope:** AWS, Terraform, CI/CD, Nginx, Celery, Redis, Kubernetes.

**Completion evidence**

- `docker compose up --build` starts Django and PostgreSQL
- both services become healthy
- migrations complete successfully
- Swagger is reachable
- the container runs as a non-root user
- the complete automated test suite remains green

**Branch:** `feature/task-004-app-containerization`

**Commit:** `feat: containerize django application`

---

## TASK-005 — GitHub Actions CI

**Goal:** Validate every pull request and push to `main`.

**Scope**

- uv-based dependency setup
- PostgreSQL CI service
- lockfile validation
- Ruff format and lint checks
- Django system checks
- migration drift checks
- complete PostgreSQL-backed tests
- OpenAPI schema validation
- Docker image build
- dependency caching
- minimal workflow permissions

**Completion evidence:** pull requests show green checks and broken changes fail automatically.

**Branch:** `feature/task-005-github-actions-ci`

**Commit:** `ci: add application validation workflow`

---

## TASK-006 — Terraform bootstrap and remote state

**Goal:** Establish the Terraform structure and safe remote state.

**Scope**

- Terraform and AWS provider version constraints
- reusable naming and tagging
- S3 remote-state bucket
- encryption, versioning, and public-access blocking
- approved state-locking mechanism
- main backend configuration
- formatting, validation, and planning commands
- state recovery documentation

**Important:** verify the current recommended Terraform state-locking method before implementation.

**Completion evidence:** remote state works and no state file is committed.

**Branch:** `feature/task-006-terraform-bootstrap`

**Commit:** `infra: bootstrap terraform remote state`

---

## TASK-007 — AWS network foundation

**Goal:** Create the reusable AWS network.

**Scope**

- VPC
- public and private subnets across at least two availability zones
- route tables
- internet gateway
- NAT gateway versus VPC endpoint decision
- least-privilege security groups
- network outputs and documentation
- recurring-cost review before apply

**Completion evidence:** private database subnets are isolated and the network flow is documented.

**Branch:** `feature/task-007-aws-network`

**Commit:** `infra: add aws network foundation`

---

## TASK-008 — ECR and image publishing

**Goal:** Store and publish versioned application images.

**Scope**

- Terraform-managed ECR repository
- image scanning
- encryption
- lifecycle rules
- image-tag policy
- GitHub OIDC
- least-privilege publish permissions
- CI image build and push

**Completion evidence:** CI publishes a traceable image without long-lived AWS keys.

**Branch:** `feature/task-008-ecr-image-pipeline`

**Commit:** `infra: add ecr image publishing`

---

## TASK-009 — RDS PostgreSQL

**Goal:** Provision the managed application database.

**Scope**

- private DB subnet group
- RDS PostgreSQL
- encryption
- backups and retention
- deletion-protection decision
- Secrets Manager credentials
- least-privilege connectivity
- cost review
- operational documentation

**Completion evidence:** only the approved application security group can reach the database.

**Branch:** `feature/task-009-rds-postgresql`

**Commit:** `infra: provision managed postgresql`

---

## TASK-010 — ECS Fargate deployment

**Goal:** Deploy Django as an ECS Fargate service.

**Scope**

- ECS cluster
- task execution and application roles
- task definition
- Secrets Manager injection
- CloudWatch logs
- Application Load Balancer
- target group and health checks
- ECS service across availability zones
- one-off migration task
- deployment rollback settings

**Completion evidence:** the API and Swagger are reachable through the load balancer and tasks remain healthy.

**Branch:** `feature/task-010-ecs-fargate`

**Commit:** `infra: deploy application to ecs fargate`

---

## TASK-011 — Automated ECS deployment

**Goal:** Deploy approved revisions safely from GitHub Actions.

**Scope**

- GitHub OIDC authentication
- unique image tags
- ECR push
- ECS task-definition revision
- service deployment
- wait for stability
- failure visibility and rollback
- commit-to-image traceability

**Completion evidence:** an approved merge deploys without permanent AWS credentials.

**Branch:** `feature/task-011-ecs-deployment-pipeline`

**Commit:** `ci: add ecs deployment workflow`

---

## TASK-012 — Domain and TLS

**Goal:** Expose the platform through HTTPS.

**Scope**

- Route 53 record
- ACM certificate
- certificate validation
- HTTPS listener
- HTTP-to-HTTPS redirect
- Django host and trusted-origin settings

**Completion evidence:** the application is reachable securely through the intended domain.

**Branch:** `feature/task-012-domain-tls`

**Commit:** `infra: add domain and tls`

---

## TASK-013 — Observability and operations

**Goal:** Make the deployed platform diagnosable.

**Scope**

- structured application logging
- CloudWatch log retention
- ECS, ALB, and RDS alarms
- optional SNS notification channel
- operational runbook
- restart, rollback, connectivity, and secret-rotation procedures
- budget and cost-monitoring references

**Completion evidence:** failures are visible and have documented response steps.

**Branch:** `feature/task-013-observability`

**Commit:** `ops: add platform observability`

---

## TASK-014 — Autoscaling and resilience

**Goal:** Improve availability and capacity handling.

**Scope**

- ECS service autoscaling
- scaling metrics and limits
- health-check tuning
- deployment circuit breaker
- graceful shutdown
- database connection-limit review
- controlled load test
- cost implications

**Completion evidence:** controlled load scales the service without exceeding database limits.

**Branch:** `feature/task-014-resilience-autoscaling`

**Commit:** `ops: add ecs autoscaling and resilience`

---

## TASK-015 — Security and production readiness

**Goal:** Perform the final hardening and release review.

**Scope**

- least-privilege IAM review
- secret-management and rotation review
- network exposure review
- Django production-settings review
- JWT and rate-limiting review
- dependency and container scanning
- backup/restore verification
- disaster-recovery notes
- teardown and cost-control procedure
- final architecture and README update

**Completion evidence:** the deployed platform is reproducible, documented, recoverable, and has no unresolved critical findings.

**Branch:** `feature/task-015-production-readiness`

**Commit:** `docs: complete production readiness review`

---

## Dependency ladder

```text
TASK-004  Containerized local application
    ↓
TASK-005  CI validation and Docker build
    ↓
TASK-006  Terraform remote state
    ↓
TASK-007  AWS network
    ↓
TASK-008  ECR image pipeline
    ↓
TASK-009  RDS PostgreSQL
    ↓
TASK-010  ECS Fargate deployment
    ↓
TASK-011  Automated deployment
    ↓
TASK-012  Domain and TLS
    ↓
TASK-013  Observability
    ↓
TASK-014  Autoscaling and resilience
    ↓
TASK-015  Production-readiness review
```

TASK-008 and TASK-009 can partly proceed in parallel after TASK-007, but the order above minimizes rework.

---

## Rules for every future task

1. Start from a clean, updated `main`.
2. Create one feature branch.
3. Create or update the permanent task specification before implementation.
4. Use a fresh Codex session.
5. Ask Codex to inspect and plan before editing.
6. Store Codex plans and reports only as temporary untracked Markdown files.
7. Keep `AGENTS.md` local-only.
8. Review the plan before approving implementation.
9. Run automated checks before manual verification.
10. Record final decisions and results in the permanent task document.
11. Delete temporary reports before staging.
12. Stage only intended files.
13. Review the staged diff.
14. Commit through a pull request.
15. Review the GitHub diff before merging.
16. Sync `main` and clean branches after merge.

---

## Immediate next action

Create the permanent specification:

```text
docs/tasks/TASK-004-django-containerization.md
```

Create the feature branch:

```text
feature/task-004-app-containerization
```

The first Codex turn should inspect the current Compose configuration, Django settings, uv workflow, Docker/WSL environment, health-check requirements, and container security practices. It should produce a plan without editing files.
