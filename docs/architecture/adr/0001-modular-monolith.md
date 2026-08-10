# ADR-0001: Modular Monolith

## Status

Accepted

## Context

LifeLink AI has multiple domains (auth, vault, trusted contacts, emergency, notifications,
audit, AI, admin). We need clean domain boundaries that can later be split into services
without a big-bang rewrite, while keeping the initial deployment simple.

## Decision

Build a modular monolith: a single FastAPI application with clearly separated domain modules,
each with its own service/repository/schema layers. Modules communicate through the service
layer, never through direct database access from other modules.

## Consequences

- Simpler local development and one deployment unit.
- Clear seams for future extraction into microservices.
- Requires disciplined dependency direction between modules.
