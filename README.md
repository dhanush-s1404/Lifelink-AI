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
- [ ] **M2** — Backend Foundation
- [ ] **M3** — Database & Migrations
- [ ] **M4** — Authentication
- [ ] **M5** — User Management
- [ ] **M6** — Frontend Foundation
- [ ] **M7** — Dashboard
- [ ] **M8** — Vault
- [ ] **M9** — Vault Items
- [ ] **M10** — Document Storage
- [ ] **M11** — Trusted Contacts
- [ ] **M12** — Access Control
- [ ] **M13** — Emergency Workflow
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

| Layer         | Technology                                                          |
| ------------- | ------------------------------------------------------------------- |
| Frontend      | Next.js, React, TypeScript, Tailwind CSS, TanStack Query, Zod, RHF  |
| Backend       | Python, FastAPI, Pydantic, SQLAlchemy 2.x, Alembic                  |
| Database      | PostgreSQL                                                          |
| Cache / Queue | Redis (Celery broker & result backend)                              |
| Jobs          | Celery                                                              |
| Storage       | S3-compatible object storage (MinIO for local dev)                  |
| Auth          | JWT access + rotating refresh tokens, Argon2id, MFA-ready, RBAC     |
| AI            | Provider abstraction, Gemini provider, embeddings / RAG             |
| Infra         | Docker, Docker Compose, Nginx, GitHub Actions                       |
| Testing       | Pytest, pytest-asyncio, Playwright, API integration tests           |
| Quality       | Ruff, Black, MyPy, ESLint, Prettier                                 |
| Observability | Structured logging, Prometheus, Grafana, OpenTelemetry-ready        |

## Product Highlights

- **Secure digital vault** for identity, insurance, financial, medical, legal, and property data
- **Trusted contacts & beneficiaries** with explicit, scoped access
- **Emergency workflow** — verified requests release *only* authorized information, time-limited
- **Granular permissions** — least privilege, ownership checks
- **AI assistant** that searches only what the caller is authorized to see
- **Full audit trail** for every security-sensitive action
- **Admin panel** that never sees decrypted user vault content

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

## Documentation

- [Architecture](docs/architecture/)
- [Security & threat model](docs/security/)
- [Database](docs/database/)
- [API](docs/api/)
- [Deployment](docs/deployment/)
- [Development](docs/development/)

## License

Proprietary / all rights reserved.
