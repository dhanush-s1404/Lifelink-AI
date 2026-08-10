SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help setup dev down logs backend frontend lint format test typecheck migrate seed clean

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

setup: ## Install everything for local development
	cd backend && python -m venv .venv && .venv/Scripts/pip install -e ".[dev]" || .venv/bin/pip install -e ".[dev]"
	cd frontend && npm install

dev: ## Run the full stack via docker compose
	docker compose up --build

down: ## Stop the stack
	docker compose down

logs: ## Tail logs
	docker compose logs -f

backend: ## Run backend locally (outside docker)
	cd backend && .venv/Scripts/uvicorn app.main:app --reload --port 8000

frontend: ## Run frontend locally (outside docker)
	cd frontend && npm run dev

lint: ## Lint backend + frontend
	cd backend && .venv/Scripts/ruff check . || .venv/bin/ruff check .
	cd frontend && npm run lint

format: ## Format backend + frontend
	cd backend && .venv/Scripts/black . || .venv/bin/black .
	cd frontend && npm run format

test: ## Run backend tests
	cd backend && .venv/Scripts/pytest || .venv/bin/pytest

typecheck: ## Type-check backend + frontend
	cd backend && .venv/Scripts/mypy app || .venv/bin/mypy app
	cd frontend && npm run typecheck

migrate: ## Apply database migrations
	cd backend && .venv/Scripts/alembic upgrade head || .venv/bin/alembic upgrade head

seed: ## Seed the database with sample data
	cd backend && .venv/Scripts/python -m app.scripts.seed || .venv/bin/python -m app.scripts.seed

clean: ## Remove caches
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".next" -type d -exec rm -rf {} + 2>/dev/null || true
