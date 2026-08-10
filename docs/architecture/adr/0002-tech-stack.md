# ADR-0002: Technology Stack

## Status

Accepted

## Context

The project must demonstrate transferable professional skills, with Python as the primary
backend language. The stack must be mainstream, well-tested, and justify every choice.

## Decision

- Backend: Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic.
- Database: PostgreSQL.
- Cache/queue: Redis, Celery.
- Object storage: S3-compatible (MinIO locally).
- Auth: JWT access + rotating refresh tokens, Argon2id.
- AI: provider abstraction with a Gemini provider and a mock provider.
- Frontend: Next.js + React + TypeScript + Tailwind + TanStack Query + Zod + React Hook Form.
- Infra: Docker Compose, Nginx, GitHub Actions.

## Consequences

- Broad ecosystem, excellent tooling and hiring value.
- Mature async ecosystem for FastAPI.
- Gemini chosen for the first AI provider due to cost/ease; abstraction allows swapping.
