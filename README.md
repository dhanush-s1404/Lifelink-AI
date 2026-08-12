# LifeLink AI

Digital Emergency Vault & Digital Legacy Platform

LifeLink AI is a secure, production-grade SaaS application that lets people store the important
information their family or trusted contacts may need during a death, hospitalization,
incapacitation, or other emergency — and controls exactly who can see what, and when.

> This is a serious, portfolio-grade project. It is built with real engineering discipline:
> Clean Architecture, security-first design, automated testing, CI/CD, Docker, and observability.

---

## Status

Development in progress — milestone-driven build.

- [x] **M1** — Project Foundation
- [x] **M2** — Backend Foundation
- [x] **M3** — Database & Migrations
- [x] **M4** — Authentication
- [x] **M5** — User Management
- [x] **M6** — Frontend Foundation
- [x] **M7** — Dashboard
- [x] **M8** — Vault
- [x] **M9** — Vault Items
- [x] **M10** — Document Storage
- [x] **M11** — Trusted Contacts
- [x] **M12** — Access Control
- [x] **M13** — Emergency Workflow
- [ ] **M14** — Notifications
- [ ] **M15** — Audit System
- [ ] **M16** — AI Foundation
- [ ] **M17** — AI Assistant
- [ ] **M18** — Search
- [ ] **M19** — Security Hardening
- [ ] **M20** — Admin Panel
- [ ] **M21** — Testing
- [ ] **M22** — Docker
- [ ] **M23** — CI/CD
- [ ] **M24** — Monitoring
- **M25** — Production Hardening

## Technology Stack

| Layer         | Technology                                                         |
| ------------- | ------------------------------------------------------------------ |
| Frontend      | Next.js, React, TypeScript, Tailwind CSS, TanStack Query, Zod, RHF |
| Backend       | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic                 |
| Database      | PostgreSQL                                                         |
| Cache / Queue | Redis (Celery broker & result backend)                             |
| Jobs          | Celery                                                             |
| Storage       | S3-compatible object storage (MinIO for local dev)                 |
| Auth          | JWT access + rotating refresh tokens, Argon2id, MFA-ready, RBAC    |
| AI            | Provider abstraction, Gemini provider, embeddings / RAG            |
| Infra         | Docker, Docker Compose, Nginx, GitHub Actions                      |
| Testing       | Pytest, pytest-asyncio, Playwright, API integration tests          |
| Quality       | Ruff, Black, MyPy, ESLint, Prettier                                |
| Observability | Structured logging, Prometheus, Grafana, OpenTelemetry-ready       |

## Product Highlights

- **Secure digital vault** for identity, insurance, financial, medical, legal, and property data
- **AES-256-GCM encryption at rest** — vault content is encrypted before it touches the database; only the owner can decrypt it
- **Trusted contacts & beneficiaries** with explicit, scoped access and **mutual consent** (owner invites, contact accepts)
- **Emergency workflow** — a trusted contact raises an emergency; after a configurable grace period with no owner response, it escalates and releases read access to the vault to that contact only
- **Granular permissions** — least privilege, ownership checks, per-contact emergency/access toggles
- **Version history** — every vault item edit creates an immutable snapshot
- **AI assistant** that searches only what the caller is authorized to see *(planned)*
- **Full audit trail** for every security-sensitive action *(planned)*
- **Admin panel** that never sees decrypted user vault content *(planned)*

## Repo Layout

```
lifelink-ai/
├── frontend/        # Next.js + TypeScript + Tailwind
├── backend/         # FastAPI application (modular monolith)
├── infrastructure/  # Docker, monitoring, storage configs
├── nginx/           # Reverse proxy configs
├── scripts/         # Dev/ops helper scripts
├── docs/            # Architecture, security, API, deployment docs
├── tests/           # Top-level / end-to-end test material
└── .github/         # CI/CD workflows
```

## Quick Start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API / Swagger: http://localhost:8000/docs
- MinIO console: http://localhost:9001

See [docs/deployment/docker.md](docs/deployment/docker.md) for details.

## API Surface (implemented)

All endpoints live under `/api/v1` and require a `Bearer` access token unless noted.

| Area | Endpoints |
| ---- | --------- |
| Auth | `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/password-reset/request\|confirm`, `/auth/verify-email/request\|confirm`, `GET /auth/sessions` |
| Users | `GET/PATCH /users/me`, `POST /users/me/password` |
| Vaults | `GET/POST /vaults`, `GET/PATCH/DELETE /vaults/{id}`, `GET/POST /vaults/{id}/categories`, `GET/POST /vaults/{id}/items`, `GET/PATCH/DELETE /vaults/{id}/items/{item_id}`, `GET .../items/{item_id}/versions` |
| Contacts | `GET/POST /contacts`, `GET /contacts/incoming`, `POST /contacts/{id}/accept\|decline`, `PATCH/DELETE /contacts/{id}` |
| Emergency | `POST /emergencies`, `GET /emergencies`, `GET /emergencies/activated`, `GET /emergencies/{id}`, `POST /emergencies/{id}/confirm\|cancel`, `GET /emergencies/{id}/release` |
| Dashboard | `GET /dashboard/summary` |
| System | `GET /health`, `/ready`, `/live`, `/api/v1/ping` |

Interactive docs: `http://localhost:8000/docs` (Swagger UI).

## Documentation

- [Architecture](docs/architecture/)
- [Security & threat model](docs/security/)
- [Database](docs/database/)
- [API](docs/api/)
- [Deployment](docs/deployment/)
- [Development](docs/development/)

## License

Proprietary / all rights reserved.

opencode -s ses_0144d5e0dffeOig6mNWBBuEm1N
