# Database Documentation

LifeLink AI uses PostgreSQL with SQLAlchemy 2.x ORM and Alembic migrations.

- [Schema](schema.md) — entity overview (written out as the schema stabilizes).
- Migrations live in `backend/alembic/versions/`.

## Rules

- Every schema change gets an Alembic migration.
- Use UUID primary keys, timestamps, foreign keys, unique + check constraints, and indexes.
- Use soft deletion where appropriate.
- Transactions are used for multi-statement operations.
