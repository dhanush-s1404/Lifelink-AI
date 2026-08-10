# Development Guide

## Environment

- Python 3.12+ (backend), Node 20+ (frontend)
- See [docs/architecture/adr/0002-tech-stack.md](../architecture/adr/0002-tech-stack.md)

## Setup

```bash
# one-time
cp .env.example .env
make setup          # backend venv + frontend deps
make dev            # full docker compose stack
```

## Commands

| Task         | Command                 |
| ------------ | ----------------------- |
| Run backend  | `make backend`          |
| Run frontend | `make frontend`         |
| Tests        | `make test`             |
| Lint         | `make lint`             |
| Type check   | `make typecheck`        |
| Migrate      | `make migrate`          |
| Seed         | `make seed`             |

## Working on the backend

- Run migrations after any model change: `alembic revision --autogenerate -m "..."`, then `alembic upgrade head`.

## Working on the frontend

- Feature-based organization under `frontend/src/features/`.
- API calls go through typed client wrappers using TanStack Query.

## Quality gates

1. `ruff check .`
2. `black .`
3. `mypy app`
4. `pytest`
5. `npm run lint`
6. `npm run typecheck`
