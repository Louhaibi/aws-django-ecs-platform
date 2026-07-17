# Contributing

Thank you for your interest in contributing to this project.

## Development setup

1. Clone the repository.
2. Install Python 3.13, `uv`, and Docker Desktop.
3. Move to the application directory:

   ```powershell
   cd app
   ```

4. Create the local environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

5. Start PostgreSQL:

   ```powershell
   docker compose up -d --wait db
   ```

6. Synchronize the locked dependencies:

   ```powershell
   uv sync --locked --all-groups
   ```

7. Apply database migrations:

   ```powershell
   uv run python manage.py migrate
   ```

8. Run the Django development server:

   ```powershell
   uv run python manage.py runserver
   ```

The Django Admin interface is available at:

```text
http://127.0.0.1:8000/admin/
```

Create a local administrator when needed:

```powershell
uv run python manage.py createsuperuser
```

## Development workflow

1. Update the local `main` branch.
2. Create a focused feature branch.
3. Keep each change limited to one clear purpose.
4. Add or update tests for behavior changes.
5. Update documentation when setup, behavior, or architecture changes.
6. Run all required checks.
7. Review the complete Git diff.
8. Open a pull request against `main`.

Example:

```powershell
git switch main
git pull --ff-only origin main
git switch -c feature/short-description
```

## Required checks

Run the following commands from the `app` directory:

```powershell
uv lock --check
uv run ruff format --check .
uv run ruff check .
uv run python manage.py check
uv run python manage.py makemigrations --check --dry-run
uv run pytest
uv run python manage.py spectacular --validate --file .tmp-task-003-schema.yml
```

Inspect the schema result and remove the generated `.tmp-task-003-schema.yml` after validation.

When a change includes new migrations, also run:

```powershell
docker compose up -d --wait db
uv run python manage.py migrate
```


## Manual verification

Behavior changes should also be verified manually after the automated checks pass.

The pull request should explain:

1. how to start the required services;
2. which page, command, or interface to open;
3. what behavior should be observed;
4. how to stop the services safely;
5. whether local test data remains afterward.

For Django model and Admin changes, verify the behavior through:

```text
http://127.0.0.1:8000/admin/
```

For API changes, include example requests and the API documentation URL. Swagger UI is available at:

```text
http://127.0.0.1:8000/api/docs/
```

Use local-only users and tokens. Do not paste access tokens, refresh tokens, or signing keys into pull requests, issues, screenshots, or documentation.

## Commit messages

Use clear and focused commit messages.

Examples:

```text
feat: add project membership validation
fix: reject invalid task assignments
test: cover project access rules
docs: update local development instructions
chore: update development tooling
```

## Pull requests

Pull requests should describe:

- the problem being solved;
- the implementation approach;
- how the change was tested;
- manual verification steps;
- security, operational, or cost implications;
- known limitations or follow-up work.

Keep pull requests focused and avoid combining unrelated changes.

## Repository hygiene

Do not commit:

- `.env` files;
- credentials or access tokens;
- virtual environments;
- Python cache directories;
- test and lint caches;
- local database files;
- generated development data;
- editor-specific temporary files.

Stop the local PostgreSQL service when it is no longer needed:

```powershell
docker compose stop db
```

This keeps the named volume and local development data.

To intentionally remove the local database data:

```powershell
docker compose down --volumes
```

This command permanently deletes the local PostgreSQL volume and should only be used for an intentional reset.
