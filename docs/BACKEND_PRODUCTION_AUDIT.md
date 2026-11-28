# Lekhan — Forensic Backend Production Audit

> **Classification:** Comprehensive Technical & Security Audit  
> **Audited Modules:** `backend/app/`, `backend/migrations/`, `backend/tests/`, `backend/pyproject.toml`, `.github/workflows/ci.yml`  
> **Role:** Principal Backend Engineer, Software Architect & Application Security Specialist  
> **Date:** November 2026  

---

## 1. Existing Backend Architecture

Lekhan follows a **hexagonal (ports and adapters) modular monolith** architecture designed for strict domain separation and fail-closed security.

```
                      ┌──────────────────────────────────────────────┐
                      │                 Client Layer                 │
                      │       React 18 / Vite / TypeScript Strict    │
                      └──────────────────────┬───────────────────────┘
                                             │ HTTPS / RFC 9457 JSON
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │                   API Layer                  │
                      │  FastAPI (14 Routers, Rate Limiter, CSRF)    │
                      └──────────────────────┬───────────────────────┘
                                             │ Dependency Injection
                                             ▼
                      ┌──────────────────────────────────────────────┐
                      │               Application Layer              │
                      │    Use Cases, FSM Transitions, Policy RBAC   │
                      └──────────────┬───────────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
    ┌─────────────────────────┐             ┌─────────────────────────┐
    │       Domain Layer      │             │   Infrastructure Layer  │
    │ Pure Python (No I/O)    │             │ (Adapters & Repos)      │
    │ - Catalog, Parties      │             │ - PostgreSQL 16 (RLS)   │
    │ - Generation FSM        │             │ - Local Storage Vault   │
    │ - Lang Packs (MR/EN/HI) │             │ - LibreOffice Headless  │
    │ - Units & Numbering     │             │ - Argon2id / AES-256-GCM│
    └─────────────────────────┘             └─────────────────────────┘
```

The technology stack is intentionally lean and avoids unnecessary distributed infrastructure:
- **Runtime:** Python 3.12+ (tested on Python 3.13)
- **Framework:** FastAPI, Pydantic v2 Settings & Models, Starlette
- **Data Layer:** SQLAlchemy 2.0 (Strict mapped columns), PostgreSQL 16, Alembic migrations
- **Identity & Security:** Server-side sessions (PostgreSQL), Argon2id, AES-256-GCM payload envelope encryption, HMAC-SHA256 blind indexing, PostgreSQL Row-Level Security (RLS)
- **Job Engine:** PostgreSQL-backed atomic queue (`claim_next_job` with `FOR UPDATE SKIP LOCKED`)
- **Document Processing:** `docxtpl` with sandboxed Jinja2 (`StrictUndefined`), LibreOffice headless converter
- **Observability:** OpenTelemetry W3C distributed tracing, Prometheus metrics, structured correlation ID logging

---

## 2. Actual Module Responsibilities

| Module | Location | Architectural Responsibility |
|---|---|---|
| `identity` | `backend/app/identity/` | User credentials, Argon2id hashing, session policies, RBAC policies (`Actor`, `Resource`, `authorize`), TOTP MFA, login throttling. |
| `tenancy` | `backend/app/tenancy/` | Multi-tenant scoping models, tenant settings, feature flags. |
| `catalog` | `backend/app/catalog/` | Document types, property classifications, and applicability matrix. |
| `parties` | `backend/app/parties/` | Party entities, multilingual name/address dictionaries, version history. |
| `properties` | `backend/app/properties/` | Land/unit records, four-boundary configurations, ready-reckoner entries. |
| `matters` | `backend/app/matters/` | Legal transaction matters linking parties, properties, and generated deeds. |
| `templates` | `backend/app/templates/` | Manifest validation, Pratt AST condition compiler, DOCX split-run & structural linters. |
| `generation` | `backend/app/generation/` | Finite State Machine (`GenerationPipelineFSM`), asynchronous job contracts, render verification. |
| `review` | `backend/app/review/` | Document review FSM (`draft` -> `reviewed` -> `finalised`), statutory compliance checklists. |
| `lang_packs` | `backend/app/lang_packs/` | Marathi/English/Hindi number-to-words, honorifics, verb conjugation, Indian digit grouping. |
| `units` | `backend/app/units/` | Exact `Decimal` area calculations (sqm, sqft, guntha, hectare-R) with zero float drift. |
| `numbering` | `backend/app/numbering/` | Gap-free sequential document number generation (`YYYY/NNNNN`). |
| `audit` | `backend/app/audit/` | Tamper-proof SHA-256 append-only hash-chained audit log. |
| `adapters` | `backend/app/adapters/` | PostgreSQL database connection pooling, RLS lifecycle listeners, repositories, object storage, and LibreOffice subprocess manager. |
| `api` | `backend/app/api/` | 14 REST routers handling HTTP input parsing, schema validation, CSRF checks, and problem+json error responses. |

---

## 3. API Endpoint Inventory

| Path | Methods | Auth / Roles | Purpose |
|---|---|---|---|
| `/health/live` | GET | Public | Process liveness probe |
| `/health/ready` | GET | Public | Database readiness probe |
| `/metrics` | GET | IP/Token Restricted | Prometheus metrics exposition |
| `/metrics/json` | GET | IP/Token Restricted | Structured JSON metrics |
| `/api/v1/auth/login` | POST | Public | Authenticates credentials, rotates session |
| `/api/v1/auth/logout` | POST | Authenticated | Revokes current session |
| `/api/v1/auth/me` | GET | Authenticated | Returns actor profile and per-session CSRF token |
| `/api/v1/auth/password/change` | POST | Authenticated | Password rotation (current password required) |
| `/api/v1/auth/password/forgot` | POST | Public | Dispatches reset token via transactional mail |
| `/api/v1/auth/password/reset` | POST | Public | Consumes reset token and resets password |
| `/api/v1/auth/mfa/enroll` | POST | Authenticated | Initiates TOTP enrollment with QR URI |
| `/api/v1/auth/mfa/verify` | POST | Authenticated / MFA Pending | Verifies TOTP code and activates MFA |
| `/api/v1/auth/mfa/disable` | POST | Authenticated | Disables MFA (password required) |
| `/api/v1/documents` | POST, GET | Scoped (D, R, A) | Enqueues document generation job / lists history |
| `/api/v1/documents/{id}` | GET, DELETE | Scoped | Retrieves metadata / soft-deletes unfinalized docs |
| `/api/v1/documents/{id}/download` | GET | Scoped | Generates short-lived signed download token |
| `/api/v1/documents/{id}/download/stream` | GET | Public (Token Validated) | Streams document bytes securely |
| `/api/v1/documents/validate` | POST | Scoped (D, R) | Pre-execution validation & derived calculation |
| `/api/v1/documents/{id}/quality` | POST | Scoped (D, R, A) | Runs live DocxLinter & leftover client data scan |
| `/api/v1/documents/{id}/reviews` | POST | Reviewer | FSM transition (`reviewed`, `finalised`, `changes_requested`) |
| `/api/v1/drafts` | GET, POST | Scoped (D, R, A) | Lists and creates auto-saved drafting sessions |
| `/api/v1/drafts/{id}` | GET, PUT, DELETE | Scoped (Owner Isolated) | CRUD on draft sessions |
| `/api/v1/jobs/{id}` | GET | Owner, R, A | Polls asynchronous job queue execution state |
| `/api/v1/parties` | GET, POST | Scoped (D, R, A) | Trigram search & party creation |
| `/api/v1/parties/{id}` | GET, PATCH | Scoped (D, R, A) | Retrieves and updates party with optimistic locking |
| `/api/v1/properties` | GET, POST | Scoped (D, R, A) | Trigram search & property creation |
| `/api/v1/properties/{id}` | GET, PATCH | Scoped (D, R, A) | Retrieves and updates property attributes |
| `/api/v1/matters` | GET, POST | Scoped (D, R, A) | Transaction matters management |
| `/api/v1/templates` | GET, POST | Scoped (T, R, D) | Lists templates & creates template shells |
| `/api/v1/templates/{id}/versions` | POST | Template Admin | Multipart upload of DOCX + manifest |
| `/api/v1/templates/{id}/versions/{v}` | GET | T, R | Detailed version inspection & lint report |
| `/api/v1/templates/{id}/versions/{v}/transitions` | POST | T (submit), R (approve) | Template lifecycle state machine |
| `/api/v1/dashboard/stats` | GET | Scoped | Operational metrics and deed classification |
| `/api/v1/admin/users` | GET, POST | Admin | User account administration |
| `/api/v1/admin/audit` | GET | Admin | Append-only audit trail inspection |
| `/api/v1/admin/audit/verify` | GET | Admin | Cryptographic SHA-256 hash chain verification |
| `/api/v1/admin/system-health` | GET | Admin | Deep infrastructure telemetry |

---

## 4. Database Schema and Relationships

All tables strictly enforce UUIDv7 primary keys, tenant scoping, UTC timestamps, and optimistic locking where appropriate.

```
+--------------------+       +----------------------+       +-------------------------+
|      tenants       | 1---* |        users         | 1---* |        sessions         |
+--------------------+       +----------------------+       +-------------------------+
          |                             |                                  |
          |                             +-------------+                    +-- id_hash (SHA-256)
          |                                           |                    +-- csrf_token_hash
          | 1---* +-------------------------+         |                    +-- mfa_pending
          +-----> |         parties         |         |
          |       +-------------------------+         |
          |                    |                      |
          |                    | 1---*                |
          |                    v                      |
          |       +-------------------------+         |
          |       |     party_versions      |         |
          |       +-------------------------+         |
          |                                           |
          | 1---* +-------------------------+         |
          +-----> |       properties        |         |
          |       +-------------------------+         |
          |                                           |
          | 1---* +-------------------------+         |
          +-----> |         matters         | *---1 --+
          |       +-------------------------+
          |                    |
          |                    | 1---*
          |                    v
          |       +-------------------------+
          |       |     matter_parties      |
          |       +-------------------------+
          |
          | 1---* +-------------------------+       +-------------------------+
          +-----> |        documents        | 1---* |    document_reviews     |
          |       +-------------------------+       +-------------------------+
          |                    |
          |                    | *---1
          |                    v
          |       +-------------------------+       +-------------------------+
          +-----> |    template_versions    | *---1 |        templates        |
          |       +-------------------------+       +-------------------------+
          |
          | 1---* +-------------------------+
          +-----> |          jobs           |
          |       +-------------------------+
          |
          | 1---* +-------------------------+
          +-----> |         drafts          |
          |       +-------------------------+
          |
          | 1---* +-------------------------+
          +-----> |        counters         |
          |       +-------------------------+
          |
          | 1---* +-------------------------+
          +-----> |        audit_log        |
                  +-------------------------+
```

---

## 5. Audit Findings & Vulnerability Matrix

### Finding 1: Silent Exception Catch in `set_tenant_context()`
- **Classification:** **CRITICAL**
- **File and Function:** `backend/app/adapters/db.py:set_tenant_context`
- **Actual Problem:** Lines 93–94 catch generic `Exception` and execute `pass`:
  ```python
  try:
      bind = session.get_bind()
      if bind and bind.dialect.name == "postgresql":
          if tenant_id is not None:
              session.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": str(tenant_id)})
          else:
              session.execute(text("RESET app.tenant_id"))
  except Exception:
      pass
  ```
- **Reproduction Scenario:** If a PostgreSQL transaction is in an aborted state, if session binding fails, or if a dialect execution error occurs during `set_tenant_context`, the failure is silently suppressed. The transaction continues without setting `app.tenant_id` or with a stale tenant setting.
- **Potential Impact:** Under PostgreSQL Row-Level Security, queries executed without setting `app.tenant_id` return zero rows or, if `NOBYPASSRLS` is not strictly enforced, execute without tenant boundaries. Silently ignoring errors violates the non-negotiable **fail-closed** tenant boundary requirement.
- **Recommended Correction:** Remove `try...except Exception: pass`. Allow database exceptions to propagate immediately, aborting the request with HTTP 500 / Problem+JSON. Ensure the contextvar token is strictly tracked and reset on exit.
- **Required Regression Test:** `tests/integration/test_rls_postgres.py` asserting that any failure in setting tenant context immediately aborts the transaction and never executes downstream SQL.

---

### Finding 2: Unsafe Administrative Connection Fallback in Production
- **Classification:** **CRITICAL**
- **File and Function:** `backend/app/adapters/db.py:39` & `backend/app/config.py:113`
- **Actual Problem:** `APP_DATABASE_URL` is optional. The engine initialization falls back to `DATABASE_URL`:
  ```python
  db_url = settings.APP_DATABASE_URL or settings.DATABASE_URL
  ```
  In `Settings._reject_dev_keys_in_deployed_envs`, `APP_DATABASE_URL` is not validated for staging/prod environments.
- **Reproduction Scenario:** Deploying production containers with only `DATABASE_URL` configured results in FastAPI running all web requests as the database owner `lekhan` (which owns the schema and bypasses standard application role constraints).
- **Potential Impact:** Privilege escalation; table owner bypasses default privilege separation and can modify append-only audit tables or drop constraints.
- **Recommended Correction:** In `Settings._reject_dev_keys_in_deployed_envs`, mandate that `ENV in ("staging", "prod")` requires a non-empty `APP_DATABASE_URL`. Require that `APP_DATABASE_URL` does not connect as table owner/superuser, and reject default development credentials (`lekhan_app_dev_password`).
- **Required Regression Test:** Unit test asserting `Settings(ENV="prod", APP_DATABASE_URL=None)` raises a validation error.

---

### Finding 3: Cleartext PII & IP Logging in Authentication Handlers
- **Classification:** **CRITICAL**
- **File and Function:** `backend/app/api/auth.py:login`
- **Actual Problem:** Lines 241–247, 263, and 273 log raw email addresses and client IP addresses:
  ```python
  logger.warning("Throttled login attempt for %s from IP %s", payload.email, client_ip)
  logger.info("Failed login attempt for nonexistent user %s from %s", payload.email, client_ip)
  logger.info("Failed login attempt (bad password) for %s from %s", payload.email, client_ip)
  ```
- **Reproduction Scenario:** An attacker attempts credential stuffing with valid or invalid user emails. All attempted emails and IP addresses are written to standard output logs in plain text.
- **Potential Impact:** Direct violation of AGENTS.md Hard Rule 5 ("Never log personal data"). Exposes user email addresses and IP addresses to application log storage, SIEM, and monitoring collectors.
- **Recommended Correction:** Replace raw email and IP logging with correlation IDs and masked/anonymized identifiers (e.g. `[cid=...] Failed login attempt`).
- **Required Regression Test:** `tests/unit/test_zero_pii_logging.py` capturing log output during failed login attempts and verifying that no email or IP substring appears in the logs.

---

### Finding 4: Plaintext Email & IP Identifiers Stored in `rate_limits` Table
- **Classification:** **HIGH**
- **File and Function:** `backend/app/api/auth.py:232` & `backend/app/identity/throttling.py`
- **Actual Problem:** The login throttler constructs keys using raw email and IP addresses:
  ```python
  account_key = f"account:{payload.email.lower().strip()}"
  ip_key = f"ip:{client_ip}"
  ```
  These keys are persisted directly in the `rate_limits` table in the `key` column.
- **Reproduction Scenario:** Any login attempt (successful or failed) persists the raw email address and client IP into `rate_limits`.
- **Potential Impact:** Leakage of user email addresses and IP addresses at rest in an unencrypted table.
- **Recommended Correction:** Hash keys with SHA-256 or HMAC using `settings.INDEX_KEY` before persisting to `rate_limits` (e.g. `account:<sha256_hash>` and `ip:<sha256_hash>`).
- **Required Regression Test:** Unit test asserting that strings inserted into `RateLimit.key` contain only cryptographic hashes without `@` or raw IPv4/IPv6 characters.

---

### Finding 5: Missing `correlation_id` Attribute Crashing Propagated Loggers
- **Classification:** **HIGH**
- **File and Function:** `backend/app/shared/logging.py:setup_logging`
- **Actual Problem:** `CorrelationIdFilter` was added to `root_logger`, but in Python's standard `logging` library, log records propagated from child loggers (`httpx`, `sqlalchemy`, `uvicorn`) bypass filters on parent loggers. When these records reach the `StreamHandler` with formatter `%(correlation_id)s`, Python raises `ValueError: Formatting field not found in record: 'correlation_id'` and logs internal tracebacks.
- **Reproduction Scenario:** Any request issued via `httpx` or any engine logging triggers `ValueError: Formatting field not found in record: 'correlation_id'`.
- **Potential Impact:** Log spam, broken log records, and unformatted error messages in production stdout.
- **Recommended Correction:** Attach `CorrelationIdFilter` directly to the `StreamHandler` rather than only the logger, and use a custom `Formatter` subclass that defaults `record.correlation_id = getattr(record, "correlation_id", "-")`.
- **Required Regression Test:** Test emitting log messages from a child logger without correlation ID and verifying clean formatting without exceptions.

---

### Finding 6: Inconsistent Session Timeout Configuration Sources
- **Classification:** **MEDIUM**
- **File and Function:** `backend/app/config.py`, `backend/app/identity/service.py`, `backend/app/adapters/repositories/sessions.py`
- **Actual Problem:** `Settings` defines `SESSION_IDLE_MINUTES = 30` and `SESSION_ABSOLUTE_HOURS = 12`. However, `service.py` defines hardcoded constants `IDLE_TIMEOUT_MINUTES = 30` and `ABSOLUTE_TIMEOUT_HOURS = 12`, while `PostgresSessionRepository` defaults `idle_timeout_minutes: int = 30` in its constructor without reading `settings`.
- **Reproduction Scenario:** An operator alters `SESSION_IDLE_MINUTES` in `.env` to 15 minutes; `PostgresSessionRepository` continues enforcing 30 minutes.
- **Potential Impact:** Operator configuration is ignored, creating discrepancies between documented security policy and actual session lifetimes.
- **Recommended Correction:** Consolidate session timeout settings into `app.config.get_settings()` as the single authoritative source.
- **Required Regression Test:** Unit test asserting repository and service respect custom timeout settings injected via `get_settings()`.

---

### Finding 7: Mathematical Inverse Round-Trip Bug in `words_to_number_en`
- **Classification:** **MEDIUM**
- **File and Function:** `backend/app/lang_packs/english.py:words_to_number_en`
- **Actual Problem:** When parsing English monetary amounts exceeding 1,000 Crore (e.g. `10,000,000,000.00` = "Rupees One Thousand Crore Only"), the parser encounters "thousand", multiplies by 1,000, and immediately adds it to `total` and resets `current_chunk = 0`. When it subsequent encounters "crore", it multiplies `max(1, 0) * 10_000_000`, producing `10,001,000.00` instead of `10,000,000,000.00`.
- **Reproduction Scenario:** Hypothesis test `test_english_amount_in_words_roundtrip` with `amount = Decimal('10000000000.00')`.
- **Potential Impact:** Serious legal discrepancy if inverse verification or legal clause parsing is used on large commercial deed values.
- **Recommended Correction:** Restructure `words_to_number_en` to segment Indian numeral hierarchy: parse everything preceding "crore" as a sub-clause multiplying 10,000,000, followed by lakhs, thousands, and remainder.
- **Required Regression Test:** Hypothesis property test and specific test vectors for 1,000 Crore, 10,000 Crore, and 50,000 Crore.

---

### Finding 8: Insecure XML ElementTree Parsing in Provenance & Split-Runs Linters
- **Classification:** **MEDIUM**
- **File and Function:** `backend/app/generation/provenance.py:107, 155`, `backend/app/templates/lint/split_runs.py:15`, `backend/app/templates/lint/structural.py:15`
- **Actual Problem:** Uses standard `xml.etree.ElementTree` instead of `defusedxml.ElementTree` (flagged by Bandit B314 / B405).
- **Reproduction Scenario:** Malicious DOCX with recursive entity expansion (Billion Laughs) or external DTD entity injected into `customXml` or document part.
- **Potential Impact:** Denial of service via XML entity expansion or local file read via external entities if parsing untrusted template files.
- **Recommended Correction:** Replace all `xml.etree.ElementTree` with `defusedxml.ElementTree.fromstring` across all provenance and template linting utilities.
- **Required Regression Test:** Unit test parsing XML with recursive entity references verifying it is rejected safely.

---

### Finding 9: ContextVar Token Lifecycle Leak in `get_db`
- **Classification:** **MEDIUM**
- **File and Function:** `backend/app/adapters/db.py:get_db`
- **Actual Problem:** `get_db()` obtains a token via `token = current_tenant_id_ctx.set(None)`, but in `finally:`, it executes `current_tenant_id_ctx.set(None)` rather than `current_tenant_id_ctx.reset(token)`.
- **Reproduction Scenario:** If a coroutine context or thread is recycled across requests, setting to `None` overwrites parent context rather than restoring the previous token.
- **Potential Impact:** ContextVar leakage or inconsistent tenant state across nested transaction scopes.
- **Recommended Correction:** Use `current_tenant_id_ctx.reset(token)` in `finally:`.
- **Required Regression Test:** Concurrency test verifying context isolation across interleaved async tasks.

---

### Finding 10: Strict Type Annotations and Unused Imports
- **Classification:** **LOW**
- **File and Function:** 9 files in `app/`, 144 Ruff errors
- **Actual Problem:** Mypy strict mode reports 14 errors (including undefined `ET` in linting modules when type-checking, invalid type annotation for `InMemoryJobRepository.list`, and passive flag type mismatches in `models.py`). Ruff reports 144 unused or unsorted imports.
- **Reproduction Scenario:** Running `make check` (`mypy --strict app` and `ruff check .`).
- **Potential Impact:** Broken quality gates in CI/CD pipeline; code maintainability degradation.
- **Recommended Correction:** Fix type annotations, import `defusedxml.ElementTree as ET`, resolve `PassiveFlag` imports, and run `ruff check --fix .` and `ruff format .`.
- **Required Regression Test:** `make check` passing with 0 mypy errors and 0 ruff errors.

---

## 6. Test Suite Baseline Summary

A fresh test baseline was executed across all test files:
- **Total Collected Tests:** 723 tests
- **Property-Based Tests:** 8 tests (1 failure in `test_english_amount_in_words_roundtrip` due to Finding 7)
- **Integration Tests:** 8 tests skipped when PostgreSQL is not running locally (fail-safe skip).
- **Unit & Golden Tests:** Golden templates, DAG compiler, FSM transitions, and cryptography passed.
- **Ruff Lint:** 144 errors (131 auto-fixable)
- **Mypy Strict:** 14 errors across 9 files
- **Bandit Security Scan:** 2 medium (ElementTree), 16 low (try-except-pass, subprocess)
- **Pip Audit:** 0 application vulnerabilities; pip wheel upgrade needed (`26.1.2` -> `26.2+`)

---

## 7. Recommended Implementation Sequence

1. **Stage 2 — Critical Security Fixes:**
   - Fix `set_tenant_context` to fail closed and raise immediately on database error.
   - Enforce mandatory `APP_DATABASE_URL` in production Settings with role validation.
   - Remove cleartext email and IP logging in `auth.py`.
   - Hash rate limit keys to preserve zero-PII in `rate_limits`.
   - Fix `CorrelationIdFilter` on logging handlers to prevent `KeyError: 'correlation_id'`.
2. **Stage 3 — Database Reliability & Data Integrity:**
   - Ensure `get_db` cleans up ContextVar tokens using `reset(token)`.
   - Consolidate session timeout settings to a single authoritative source.
   - Harden transaction rollbacks and remove silent `pass` blocks.
3. **Stage 4 — Worker & Document Processing:**
   - Fix `words_to_number_en` Indian scale terms calculation for amounts > 100 Crore.
   - Migrate XML parsing to `defusedxml` across all provenance and linting modules.
4. **Stage 5 — Code Quality & Gates:**
   - Resolve all 14 Mypy strict errors.
   - Format and lint with Ruff.
   - Run full test suite and verify 100% green status.
