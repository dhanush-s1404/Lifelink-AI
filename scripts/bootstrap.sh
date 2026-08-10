#!/usr/bin/env bash
set -euo pipefail

# LifeLink AI dev bootstrap helper.
# Usage: ./scripts/bootstrap.sh [backend|frontend|all]

cd "$(dirname "$0")/.."

if [[ -f .env ]]; then
  echo "> .env already exists, skipping"
else
  cp .env.example .env
  echo "> Created .env from .env.example (fill in real secrets!)"
fi

case "${1:-all}" in
  backend)
    cd backend
    python -m venv .venv
    if [[ -f .venv/Scripts/python ]]; then VPY=.venv/Scripts/python; else VPY=.venv/bin/python; fi
    "$VPY" -m pip install --upgrade pip
    "$VPY" -m pip install -e ".[dev]"
    ;;
  frontend)
    cd frontend
    npm install
    ;;
  all)
    "$0" backend
    "$0" frontend
    ;;
esac

echo "> Done."
