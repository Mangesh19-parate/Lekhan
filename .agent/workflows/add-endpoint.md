# Workflow: /add-endpoint

When adding or modifying an API endpoint:
1. Define Pydantic request/response schemas in domain modules (no FastAPI/SQLAlchemy imports).
2. Wire endpoint in FastAPI router under `/api/v1/`.
3. Enforce tenant scoping and `authorize(actor, action, resource)`.
4. Update `docs/API.md` with route, methods, roles, and status codes.
5. Add test to authorization matrix test suite verifying 200, 401, 403, and 404 responses across roles.
6. Run `make check`.

