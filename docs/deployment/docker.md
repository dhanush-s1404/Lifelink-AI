# Docker Deployment

## Prerequisites

- Docker + Docker Compose

## Getting started

```bash
cp .env.example .env   # then fill in real secrets
docker compose up --build
```

Services:

| Service   | Address                        |
| --------- | ------------------------------ |
| Frontend  | http://localhost:3000          |
| Backend   | http://localhost:8000          |
| API docs  | http://localhost:8000/docs     |
| MinIO S3  | http://localhost:9000          |
| MinIO UI  | http://localhost:9001          |
| Nginx     | http://localhost:80            |
| Postgres  | localhost:5432                 |
| Redis     | localhost:6379                 |

## Common commands

```bash
docker compose up --build        # start everything
docker compose down              # stop (keeps volumes)
docker compose down -v           # stop and wipe data
docker compose logs -f backend   # follow backend logs
docker compose exec backend alembic upgrade head   # migrate
```
