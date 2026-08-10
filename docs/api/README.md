# API Documentation

The API is built with FastAPI and is self-documented via OpenAPI.

- Interactive docs: `/docs` (Swagger UI) when the backend is running.
- Raw schema: `/openapi.json`
- Versioned under `/api/v1/`

## Conventions

- Consistent error envelope: `{ "error": { "code", "message", "request_id" } }`
- Pagination, filtering, and sorting on list endpoints.
- UUID identifiers throughout.
- Auth: `Authorization: Bearer <access_token>`
