# Lekhan — Production Remediation Tracker

| Defect ID | Category | Severity | Status | Summary |
|---|---|---|---|---|
| REM-001 | Persistence | P0 | RESOLVED | Worker-API Document Repository Split (Both wired to PostgresDocumentRepository) |
| REM-002 | Persistence / Compliance | P0 | RESOLVED | PostgreSQL-backed audit trail with concurrency-safe FOR UPDATE row locking |
| REM-003 | Data Integrity | P0 | RESOLVED | Atomic PostgreSQL-backed gap-free document numbering counter |
| REM-004 | Compliance / Workflow | P0 | RESOLVED | Document review persistence with PostgreSQL `document_reviews` and FSM state enforcement |
| REM-005 | Reliability / Worker | P0 | RESOLVED | Background Worker reliability, RLS-compatible job claiming, graceful SIGTERM shutdown & heartbeat |
| REM-006 | Security / Database | P0 | RESOLVED | Database Roles, dynamic database name, configurable password, RLS on drafts & document_reviews |
| REM-007 | Privacy / Security | P0 | RESOLVED | Authenticated AES-256-GCM field encryption, HMAC blind indexes, and PII masking |
| REM-008 | Security / Auth | P1 | RESOLVED | Database-backed TOTP replay prevention & trusted proxy header parsing |
| REM-009 | Auth / Functionality | P1 | RESOLVED | Implemented /auth/password/forgot (202) and /auth/password/reset with session invalidation |
| REM-010 | Security / Auth | P1 | RESOLVED | Enforced tenant-scoped Resource authorization and draft IDOR isolation for drafters |
| REM-011 | Security / Storage | P1 | RESOLVED | Document download session/token security, path-traversal prevention & audit logging |
| REM-012 | Generation / Legal | P0 | RESOLVED | Context builder, approved template validation gate (`sale_deed_plot_mr`), no fake templates |
| REM-013 | Generation / Legal | P0 | RESOLVED | Verification gate: full DOCX XML scanner for zero unrendered tags and tamper provenance |
| REM-014 | Precision / Legal | P0 | RESOLVED | Exact Python Decimal currency calculations and strict area conversion factors |
| REM-015 | Legal Workflow | P0 | RESOLVED | Mandatory statutory checklist and reviewer verification before finalization lock |
| REM-016 | Infrastructure / SRE | P0 | RESOLVED | Production Docker Compose with migrator step, Caddy SPA fallback mount, auto-secret generator |
| REM-017 | Infrastructure / SRE | P1 | RESOLVED | Comprehensive system health monitoring, error problem+json pass-through, and zero secret leakage |

---

## Remediation Details

### REM-001: Worker–API Repository Split
- **Defect:** Worker imported global singleton defaulting to `InMemoryDocumentRepository` while API used `PostgresDocumentRepository`.
- **Root Cause:** Implicit default in `GenerationPipelineFSM` construction.
- **Affected Files:**
  - `backend/app/generation/pipeline.py`
  - `backend/app/worker.py`
  - `backend/app/api/documents.py`
  - `backend/app/adapters/repositories/documents.py`
- **Architectural Correction:** Constructed worker pipeline with `PostgresDocumentRepository`. API and worker now share the same persistent database storage contract.
- **Status:** RESOLVED.

### REM-002: Audit Log Persistence
- **Defect:** Audit log used in-memory state by default and lacked concurrency locking on SHA-256 chain.
- **Root Cause:** Absence of row-level locking during audit log insertion.
- **Affected Files:**
  - `backend/app/audit/service.py`
  - `backend/app/adapters/repositories/audit.py`
- **Architectural Correction:** Wired PostgreSQL audit repository with `with_for_update()` on the tenant's latest audit log entry, serializing hash chain computation and guaranteeing tamper-proof SHA-256 integrity.
- **Status:** RESOLVED.

### REM-003: Document Numbering In-Memory State
- **Defect:** Process-local counter dictionary caused collisions across workers or process restarts.
- **Root Cause:** In-memory counter store.
- **Affected Files:**
  - `backend/app/numbering/service.py`
  - `backend/app/shared/models.py`
- **Architectural Correction:** Implemented PostgreSQL atomic UPSERT on `counters` table: `INSERT INTO counters ... ON CONFLICT (tenant_id, key, year) DO UPDATE SET value = counters.value + 1 RETURNING value;`.
- **Status:** RESOLVED.

### REM-004: Review Persistence
- **Defect:** Review metadata and checklists stored in memory dict `self._reviews`.
- **Root Cause:** Missing database persistence for review entities.
- **Affected Files:**
  - `backend/app/review/service.py`
  - `backend/app/api/review.py`
  - `backend/app/shared/models.py`
  - `backend/migrations/versions/0013_document_reviews_and_drafts_rls.py`
- **Architectural Correction:** Created `document_reviews` table in PostgreSQL with migration 0013. Integrated `DocumentReviewService` with PostgreSQL `with_for_update()` row locking, persisting reviewer, checklist, and finalizer identities.
- **Status:** RESOLVED.

### REM-005: Background Job Reliability
- **Defect:** Worker lacked graceful signal shutdown, heartbeat, and consistent error classification.
- **Affected Files:**
  - `backend/app/worker.py`
  - `backend/app/adapters/repositories/jobs.py`
- **Architectural Correction:** Added graceful `SIGTERM`/`SIGINT` handlers, periodic worker heartbeat logging, visibility timeout recovery, and dead-letter queue classification.
- **Status:** RESOLVED.

### REM-006: Database Roles and RLS Hardening
- **Defect:** Migration 0010 hardcoded database name `lekhan_db` and password. Migration 0012 omitted RLS on `drafts`.
- **Affected Files:**
  - `backend/migrations/versions/0010_rls_roles_and_functions.py`
  - `backend/migrations/versions/0013_document_reviews_and_drafts_rls.py`
- **Architectural Correction:** Migration 0010 updated to dynamically use `current_database()` and read `LEKHAN_APP_PASSWORD`. Migration 0013 created to enable RLS on `drafts` and `document_reviews`.
- **Status:** RESOLVED.

### REM-007: Authenticated PII Encryption
- **Defect:** Sensitive party PII (PAN, contacts) stored without authenticated encryption.
- **Affected Files:**
  - `backend/app/shared/crypto.py`
  - `backend/app/adapters/repositories/parties.py`
- **Architectural Correction:** Added AES-256-GCM `encrypt_field`, `decrypt_field`, `compute_blind_index`, and PII masking helpers (`mask_pan`, `mask_aadhaar`, `mask_phone`).
- **Status:** RESOLVED.

### REM-008 & REM-009: Auth Hardening & Password Recovery
- **Defect:** Missing `/auth/password/forgot` and `/auth/password/reset` endpoints; in-memory TOTP replay store.
- **Affected Files:**
  - `backend/app/api/auth.py`
- **Architectural Correction:** Implemented timed, cryptographically signed password reset tokens with session revocation; backed TOTP replay protection with PostgreSQL `rate_limits` table.
- **Status:** RESOLVED.

### REM-010: Resource Authorization & IDOR Isolation
- **Defect:** Drafts endpoints lacked resource context in `authorize()`, permitting cross-user IDOR access by drafters.
- **Affected Files:**
  - `backend/app/api/drafts.py`
  - `backend/app/identity/policy.py`
- **Architectural Correction:** Passed `Resource(tenant_id, "draft", owner_id=draft.user_id)` to all draft endpoints and restricted drafters to their own drafts.
- **Status:** RESOLVED.

### REM-016: Production Infrastructure & Operations
- **Defect:** Caddy container lacked frontend mount; docker-compose lacked automated migration step; docker secrets files missing.
- **Affected Files:**
  - `docker-compose.prod.yml`
  - `deploy/init_secrets.py`
  - `deploy/Caddyfile`
- **Architectural Correction:** Added `migrator` service in `docker-compose.prod.yml`, mounted `./frontend/dist:/srv/frontend/dist:ro` in Caddy, and added `deploy/init_secrets.py` for automated secret initialization.
- **Status:** RESOLVED.
