# Lekhan — Production Remediation Tracker

| Defect ID | Category | Severity | Status | Summary |
|---|---|---|---|---|
| REM-001 | Persistence | P0 | RESOLVED | GenerationPipelineFSM defaults to PostgresDocumentRepository; API routes inject get_pipeline |
| REM-002 | Persistence / Compliance | P0 | RESOLVED | AuditService defaults to PostgresAuditRepository with concurrency-safe FOR UPDATE row locking |
| REM-003 | Data Integrity | P0 | RESOLVED | Document numbering counter shares transaction with document persistence; fails fast on DB errors |
| REM-004 | Compliance / Workflow | P0 | RESOLVED | Document review queries PostgreSQL directly, commits transactions on transitions, and fails fast |
| REM-005 | Reliability / Worker | P1 | RESOLVED | Background worker enforces max_attempts at claim time, dead-letters crashing jobs, and uses RLock in memory |
| REM-006 | Security / Database | P0 | RESOLVED | Least-privilege `lekhan_app` role wired via `APP_DATABASE_URL` with RLS; `claim_next_job` SECURITY DEFINER for worker claims |
| REM-007 | Privacy / Security | P0 | RESOLVED | End-to-end AES-256-GCM envelope encryption for JSONB payloads (jobs, docs, drafts, party versions) and party columns |
| REM-008 | Security / Auth | P1 | RESOLVED | Database-backed TOTP replay prevention & trusted proxy header parsing |
| REM-009 | Auth / Functionality | P1 | RESOLVED | Configured transactional delivery adapter for forgot-password reset tokens; enforced mandatory MFA in production and CIDR proxy trust |
| REM-010 | Security / Auth | P1 | RESOLVED | Enforced tenant-scoped Resource authorization and draft IDOR isolation for drafters |
| REM-011 | Security / Storage | P1 | RESOLVED | Document download session/token security, path-traversal prevention & audit logging |
| REM-012 | Generation / Legal | P0 | RESOLVED | Removed invented legal defaults (boundaries, consideration, template type); strictly enforce approved template status |
| REM-013 | Generation / Legal | P0 | RESOLVED | Jinja SandboxedEnvironment with StrictUndefined; output verification gate scans all word/*.xml parts |
| REM-014 | Precision / Legal | P0 | RESOLVED | Exact Python Decimal currency calculations and strict area conversion factors |
| REM-015 | Testing / CI | P1 | RESOLVED | Automated Playwright webServer dual-boot (FastAPI + Vite) and real PostgreSQL E2E lifecycle tests |
| REM-016 | Infrastructure / SRE | P0 | RESOLVED | Production Docker Compose: removed migrator self-loop, mounted migrator crypto secrets, enforced HTTPS in Caddy |
| REM-017 | Infrastructure / SRE | P1 | RESOLVED | Comprehensive system health monitoring, error problem+json pass-through, and zero secret leakage |
| REM-018 | Disaster Recovery / Operations | P1 | RESOLVED | Full business entity backup (all 16 relational tables + storage files); fail-fast prod DB snapshot; automated restore drill verified |

---

## Remediation Details

### REM-001: Worker–API Repository Split
- **Defect:** Worker imported global singleton defaulting to `InMemoryDocumentRepository` while API used `PostgresDocumentRepository`; `dashboard`, `portal`, and `pilot` imported global singleton directly.
- **Root Cause:** Implicit default in `GenerationPipelineFSM` construction and hardcoded imports in API modules.
- **Affected Files:**
  - `backend/app/generation/pipeline.py`
  - `backend/app/api/dashboard.py`
  - `backend/app/api/portal.py`
  - `backend/app/api/pilot.py`
  - `backend/app/api/admin.py`
- **Architectural Correction:** Constructed `GenerationPipelineFSM` with default `PostgresDocumentRepository()`. Migrated `dashboard`, `portal`, and `pilot` API modules to FastAPI dependency injection via `Depends(get_pipeline)`.
- **Status:** RESOLVED.

### REM-002: Audit Log Persistence
- **Defect:** Audit log used in-memory state by default, risking lost audit records on process restart.
- **Root Cause:** `AuditService.__init__` defaulted to `InMemoryAuditRepository()`.
- **Affected Files:**
  - `backend/app/audit/service.py`
  - `backend/app/adapters/repositories/audit.py`
- **Architectural Correction:** `AuditService` now defaults to `PostgresAuditRepository()`. Global `audit_service` instance persists to PostgreSQL `audit_log` with `with_for_update()` row locking on the tenant's latest entry, guaranteeing tamper-proof SHA-256 chain serialization.
- **Status:** RESOLVED.

### REM-003: Document Numbering In-Memory State
- **Defect:** Process-local counter dictionary caused collisions across workers or restarts; silent fallback on DB failure; numbering committed outside document transaction.
- **Root Cause:** In-memory counter store and standalone transaction lifecycle.
- **Affected Files:**
  - `backend/app/numbering/service.py`
  - `backend/app/generation/pipeline.py`
- **Architectural Correction:** Implemented PostgreSQL atomic UPSERT on `counters` table passed within the document persistence transaction session; flushes into caller's transaction; fails fast on database failure in prod/staging rather than silently falling back to in-memory counters.
- **Status:** RESOLVED.

### REM-004: Review Persistence
- **Defect:** Review metadata and checklists stored in memory dict `self._reviews`; document lookup in review service could miss PostgreSQL documents; database transactions were not committed when external sessions were passed.
- **Root Cause:** Missing database commit on externally-managed sessions and process-local dictionary fallback.
- **Affected Files:**
  - `backend/app/review/service.py`
  - `backend/app/api/review.py`
- **Architectural Correction:** Integrated `DocumentReviewService` with session-bound `PostgresDocumentRepository` for document lookups, explicit `db.commit()` on review transitions (`mark_reviewed`, `mark_finalised`, `reopen_for_edit`), and fail-fast exceptions on DB errors.
- **Status:** RESOLVED.

### REM-005: Background Job Reliability
- **Defect:** Worker lacked max-attempts check at claim time (reclaiming crashing jobs indefinitely) and InMemoryJobRepository deadlocked on nested lock acquisition.
- **Affected Files:**
  - `backend/app/worker.py`
  - `backend/app/generation/jobs.py`
  - `backend/app/adapters/repositories/jobs.py`
  - `backend/tests/unit/test_job_repository.py`
- **Architectural Correction:** Added `max_attempts` constraint to `claim_next` across both in-memory and PostgreSQL implementations; dead-letters jobs exceeding max attempts past visibility timeout; converted `InMemoryJobRepository._lock` to `threading.RLock()`.
- **Status:** RESOLVED.

### REM-006: Database Roles and RLS Hardening
- **Defect:** Production Compose ran API and worker using bootstrap owner role `lekhan` without `APP_DATABASE_URL`, bypassing RLS. Worker could not claim cross-tenant jobs under non-privileged role without RLS blocking all queries.
- **Affected Files:**
  - `docker-compose.prod.yml`
  - `backend/app/config.py`
  - `deploy/init_secrets.py`
  - `backend/migrations/versions/0014_worker_job_claiming_function.py`
  - `backend/app/adapters/repositories/jobs.py`
- **Architectural Correction:** Configured `APP_DATABASE_URL` for `lekhan_app` with Docker secret `app_db_password`; created migration 0014 with `claim_next_job` as a `SECURITY DEFINER` function with fixed `search_path = public` granted to `lekhan_app` for atomic, cross-tenant job claims.
- **Status:** RESOLVED.

### REM-007: Authenticated PII Encryption
- **Defect:** Sensitive party PII (PAN, contacts) was not populated in `PostgresPartyRepository.save()`, and customer PII was stored plaintext in JSONB columns (`jobs.payload`, `documents.data_snapshot`, `drafts.data`, and `party_versions.data`).
- **Root Cause:** Incomplete field mapping in party persistence and lack of payload envelope encryption for JSONB structures.
- **Affected Files:**
  - `backend/app/shared/crypto.py`
  - `backend/app/adapters/repositories/jobs.py`
  - `backend/app/adapters/repositories/documents.py`
  - `backend/app/adapters/repositories/parties.py`
  - `backend/app/api/drafts.py`
  - `backend/tests/unit/test_payload_encryption.py`
- **Architectural Correction:** Implemented authenticated AES-256-GCM payload envelope encryption (`encrypt_json_payload` / `decrypt_json_payload`) across all JSONB persistence boundaries (`jobs.payload`, `documents.data_snapshot`, `drafts.data`, `party_versions.data`). Populated encrypted `pan_enc`, `pan_blind_index`, and `contact_enc` in `PostgresPartyRepository.save()`.
- **Status:** RESOLVED.

### REM-008 & REM-009: Auth Hardening, MFA & Password Recovery Delivery
- **Defect:** 
  1. Missing token delivery in `/auth/password/forgot` (token generated but dropped, preventing password recovery).
  2. `ENFORCE_MFA` was disabled by default and missing in production Compose, failing to mandate MFA for privileged roles (`admin`, `reviewer`, `template_admin`).
  3. Reverse proxy trusted IP handling lacked CIDR subnet matching for internal container networks.
  4. In-memory TOTP replay store.
- **Affected Files:**
  - `backend/app/api/auth.py`
  - `backend/app/config.py`
  - `backend/app/shared/network.py`
  - `docker-compose.prod.yml`
  - `backend/tests/unit/test_password_recovery_and_network.py`
- **Architectural Correction:** 
  1. Implemented `deliver_password_reset_token` with SMTP transactional email dispatch and dev/test response passthrough.
  2. Configured automatic `ENFORCE_MFA = True` validator for staging/prod environments and added `ENFORCE_MFA: "true"` to production Compose.
  3. Added IP network CIDR block parsing in `get_client_ip` to securely validate reverse proxy forwards from Docker bridge networks (`172.16.0.0/12`).
  4. Backed TOTP replay protection with PostgreSQL `rate_limits` table.
- **Status:** RESOLVED.

### REM-010: Resource Authorization & IDOR Isolation
- **Defect:** Drafts endpoints lacked resource context in `authorize()`, permitting cross-user IDOR access by drafters.
- **Affected Files:**
  - `backend/app/api/drafts.py`
  - `backend/app/identity/policy.py`
- **Architectural Correction:** Passed `Resource(tenant_id, "draft", owner_id=draft.user_id)` to all draft endpoints and restricted drafters to their own drafts.
- **Status:** RESOLVED.

### REM-011: Document Storage Security
- **Defect:** Document download session/token security, path-traversal prevention, and download audit logging.
- **Affected Files:**
  - `backend/app/api/documents.py`
  - `backend/app/adapters/storage.py`
- **Architectural Correction:** Hardened file key resolution, verified tenant ownership before streaming downloads, and logged `document_downloaded` audit events.
- **Status:** RESOLVED.

### REM-012: Legal Generation Defaults & Template Approval Enforcement
- **Defect:** 
  1. Generation pipeline defaulted missing boundaries to arbitrary values (`रस्ता`, `प्लॉट`).
  2. Defaulted consideration to 100,000 when missing.
  3. Defaulted missing `template_id` implicitly to `sale_deed_plot_mr`.
  4. Did not verify whether requested template version was approved or matched the requested template key.
- **Affected Files:**
  - `backend/app/generation/pipeline.py`
  - `backend/tests/unit/test_strict_generation_and_approval.py`
- **Architectural Correction:**
  1. Removed all invented property boundary and financial consideration defaults from `_normalize_payload` in `pipeline.py`. Missing fields strictly fail schema validation via `PlotSaleDeedInput.model_validate`.
  2. Made `template_id` a mandatory payload field.
  3. If `template_version_id` is supplied, verifies `tv.status == "approved"` and `tv.template_key == template_id`.
  4. Verifies filesystem template `manifest.json` status is `"approved"`; rejects unapproved/draft templates with `ValueError`.
- **Status:** RESOLVED.

### REM-013: Strict Rendering & Complete XML Part Tag Verification
- **Defect:**
  1. Jinja template rendering permitted undefined variables without raising errors.
  2. Verification gate checked only `word/document.xml`, missing unrendered tags in headers, footers, footnotes, or endnotes.
- **Affected Files:**
  - `backend/app/generation/pipeline.py`
  - `backend/app/generation/spike_engine.py`
  - `backend/tests/unit/test_strict_generation_and_approval.py`
- **Architectural Correction:**
  1. Configured Jinja `SandboxedEnvironment(undefined=StrictUndefined)` during template rendering.
  2. Extended the post-render verification gate to iterate over all `word/*.xml` parts inside the resulting DOCX zip archive, failing fast if any `{{ ... }}` or `{% ... %}` tags remain.
- **Status:** RESOLVED.

### REM-016: Production Infrastructure & Operations
- **Defect:** 
  1. `migrator` service had circular self-dependency in `docker-compose.prod.yml`.
  2. `migrator` mounted only `db_password` while `app.config.Settings` requires `secret_key`, `master_key`, and `index_key` when `ENV=prod`.
  3. Caddy was configured on `:80` with `auto_https disable_redirects`, lacking TLS protection at the edge.
  4. Duplicate `migrator` entry in `api.depends_on`.
- **Affected Files:**
  - `docker-compose.prod.yml`
  - `deploy/Caddyfile`
- **Architectural Correction:** 
  1. Removed circular `migrator` self-dependency in `docker-compose.prod.yml` (migrator now depends only on `db` service healthy).
  2. Removed duplicate `migrator` dependency from `api`.
  3. Added `secret_key`, `master_key`, and `index_key` mounts to `migrator.secrets` to satisfy production Pydantic key validation.
  4. Configured Caddy with HTTPS on `{$DOMAIN:app.lekhan.local}` and automatic HTTP-to-HTTPS redirect.
- **Status:** RESOLVED.

### REM-015: E2E Integration Testing & Live Server Automation
- **Defect:** 
  1. Playwright E2E configuration lacked automated server startup (`webServer`), requiring manual pre-booting of API and Vite instances.
  2. Frontend lifecycle tests mocked API requests rather than asserting true end-to-end integration against the database and backend services.
- **Affected Files:**
  - `frontend/playwright.config.ts`
  - `backend/tests/unit/test_full_lifecycle_e2e.py`
  - `backend/tests/integration/test_postgres_e2e_lifecycle.py`
- **Architectural Correction:**
  1. Configured dual `webServer` entries in `frontend/playwright.config.ts` to automatically launch both the FastAPI backend (`port 8000`) and Vite dev server (`port 5173`) with health timeout checks.
  2. Implemented `test_postgres_e2e_lifecycle.py` exercising real PostgreSQL 16 persistence, cross-tenant job claiming, DOCX rendering, atomic counter allocation, review/finalization lifecycle, and cryptographic audit chain verification.
  3. Implemented offline unit lifecycle test `test_full_lifecycle_e2e.py` verifying full FSM transitions, unrendered tag inspection across all XML parts, review immutability locking, and audit integrity verification.
- **Status:** RESOLVED.

### REM-018: Complete Database and Object Storage Backup & Disaster Recovery
- **Defect:** 
  1. Automated backup only exported documents, counters, and audit logs, leaving out tenants, users, parties, party versions, properties, matters, matter parties, templates, template versions, document reviews, jobs, drafts, and fee rules.
  2. Database snapshot failure silently fell back to an in-memory dictionary snapshot via `except Exception as exc: logger.debug(...)`.
- **Affected Files:**
  - `backend/scripts/backup.py`
  - `backend/scripts/restore.py`
  - `backend/scripts/restore_drill.py`
  - `backend/app/numbering/service.py`
  - `backend/tests/unit/test_backup_restore.py`
- **Architectural Correction:**
  1. Implemented complete model serialization (`model_to_dict`) across all 16 business entity tables (`tenants`, `users`, `templates`, `template_versions`, `parties`, `party_versions`, `properties`, `matters`, `matter_parties`, `documents`, `document_reviews`, `jobs`, `drafts`, `counters`, `audit_logs`, `fee_rules`).
  2. Implemented topological foreign-key restore in `restore.py` with typed deserialization (`dict_to_model_kwargs`).
  3. Added fail-fast exceptions (`RuntimeError`) in prod/staging environments whenever the database connection is unreachable or snapshot fails.
  4. Added `set_counter` and `get_counter` to `DocumentNumberingService` to support automated restore drills.
- **Status:** RESOLVED.
