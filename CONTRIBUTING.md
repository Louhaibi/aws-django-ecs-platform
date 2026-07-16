# Contributing

## Development workflow

1. Select one approved task from `docs/tasks/`.
2. Read `AGENTS.md`, the task specification, and relevant decision records.
3. Propose and review an implementation plan.
4. Implement only the approved scope.
5. Run the required checks.
6. Review the diff.
7. Commit with a clear message.
8. Push only reviewed work.

Changes should be small, tested, free of secrets, documented when they alter architecture or workflow, and honest about current capabilities.

Suggested commit messages:

```text
docs: document the project foundation
chore: initialize the Django toolchain
feat: add project membership API
test: cover task assignment permissions
infra: add the dev ECS service
ci: validate Terraform pull requests
```

Pull requests should explain the problem, approach, validation, security or cost implications, and remaining limitations.
