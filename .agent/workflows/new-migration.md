# Workflow: /new-migration

When creating a new database migration:
1. Ensure table includes `id uuid PRIMARY KEY`, `tenant_id uuid NOT NULL REFERENCES tenants(id)`, `created_at`, `updated_at`.
2. Use `numeric(18,2)` for money fields, never floats.
3. Use text with CHECK constraints for enums.
4. Add index for `tenant_id` and foreign keys.
5. Generate migration with Alembic (`alembic revision -m "..."`).
6. Review migration for non-destructive backwards-compatible schema changes (expand/contract).

