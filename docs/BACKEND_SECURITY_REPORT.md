# Backend Security Report: Lekhan Legal Drafting Platform

> **Role:** Principal Backend Engineer, Software Architect & Application Security Specialist  
> **Platform:** Lekhan (Multilingual Legal Drafting Platform)  
> **Date:** November 2026  
> **Standard:** Enterprise Legal Document Security & OWASP ASVS Level 2+ Compliance

---

## 1. Executive Summary

Lekhan is a multi-tenant legal drafting system that processes sensitive real-estate records, statutory IDs (Aadhaar, PAN), financial consideration amounts, and legally binding deeds. 
Security, tenant isolation, and data confidentiality supersede all other functional and non-functional requirements.

This report documents the security posture, threat model analysis, vulnerability remediation, and verification results across the Lekhan backend.

---

## 2. STRIDE Threat Model Assessment & Mitigations

| Threat Category | Potential Attack Vector | Previous Gap | Implemented Mitigation & Verification |
|---|---|---|---|
| **Spoofing** | Session hijacking, credential stuffing, cross-tenant impersonation | Plaintext rate-limit keys exposed email & IP; session idle timeouts inconsistent | Argon2id password hashing; server-side SHA-256 session tokens; HTTP-only SameSite=Lax cookies; CSRF token validation on all state mutations; privacy-preserving SHA-256 hashed rate limit keys; session idle timeout bound to `SESSION_IDLE_MINUTES` config. |
| **Tampering** | Mutation of finalized legal deeds or audit logs; XML template injection | Unrendered Jinja tag injection; standard `xml.etree.ElementTree` in linter | Cryptographic SHA-256 append-only audit trail with `SELECT ... FOR UPDATE` row locks; state machine enforcing irreversible `finalised` deed status; migration to `defusedxml.ElementTree` across all template linting and provenance analyzers. |
| **Repudiation** | User denies deed generation or approval action | Audit log entries susceptible to race conditions during parallel requests | Sequential hash-chained audit logging (`prev_hash` validation); actor UUID and tenant UUID stamped on every state transition; immutable storage keys (`sha256(content)`). |
| **Information Disclosure** | Cross-tenant data leakage via pooled DB sessions; PII leakage in logs | `set_tenant_context()` silently swallowed DB exceptions; raw emails and IPs logged on auth failure; fallback to superuser/owner DB connection | Fail-closed PostgreSQL Row-Level Security (`SET LOCAL app.current_tenant_id`); `ContextVar` token reset in request `finally:` blocks; mandatory least-privilege `APP_DATABASE_URL` runtime role (`NOBYPASSRLS`); zero-PII logging policy enforced via `CorrelationIdFormatter`. |
| **Denial of Service** | Billion Laughs XML bomb; concurrent PDF rendering saturation; memory exhaustion | Standard XML parser in linter; unconstrained counter queries | 10MB payload size limits (`MAX_REQUEST_SIZE_BYTES`); `defusedxml` entity expansion blocking; Bounded semaphore (`LIBREOFFICE_PROCESS_LIMIT=3`) with 30s timeout on headless converters; atomic PostgreSQL rate limiting. |
| **Elevation of Privilege** | Drafter accessing reviewer/admin routes; tenant context bypass | Table-owner DB role used in runtime bypassed RLS | Explicit backend RBAC authorization matrix (`authorize(actor, action, resource)`); table ownership assigned to migration role only; forward migration 0015 enforcing strong `lekhan_app` role passwords. |

---

## 3. Vulnerability Remediation Details

### 3.1 Remediated: Fail-Closed Tenant Isolation (CWE-284, CWE-653)
- **Problem:** `app/adapters/db.py:set_tenant_context` previously used a broad `try...except Exception: pass` block. If the database failed to apply `SET LOCAL app.current_tenant_id = :tenant_id` (e.g. syntax error or context variable misconfiguration), the session proceeded with tenant context unset. Under PostgreSQL RLS policies that default to permissive behavior or if RLS was bypassed, queries could leak cross-tenant data.
- **Remediation:** Removed the exception suppression. Any failure to set tenant context raises a fatal exception immediately and rolls back the session. Furthermore, `get_db()` utilizes token-based `ContextVar` management to guarantee context reset upon connection return to the pool.
- **Verification:** Unit test `test_set_tenant_context_failure_raises_immediately` in `tests/unit/test_production_backend_hardening.py` confirms that context failures abort the request immediately.

### 3.2 Remediated: Least-Privilege Application Database Connection (CWE-250)
- **Problem:** `APP_DATABASE_URL` was optional. If absent, the application initialized with `DATABASE_URL`, which is the database owner role used by Alembic migrations. The database owner bypasses RLS policies in PostgreSQL by default (`BYPASSRLS`), invalidating all tenant isolation guarantees. Additionally, historical migration 0010 included a default development password.
- **Remediation:**
  - Added strict validation in `app/config.py`: In staging and production environments, `APP_DATABASE_URL` is mandatory, must differ from `DATABASE_URL`, and cannot contain default dev passwords (`lekhan_app_dev_password`, `change-me`, `dev-`).
  - Implemented forward-only migration `0015_harden_app_role_password.py` that dynamically alters the `lekhan_app` role password to match the `LEKHAN_APP_PASSWORD` environment secret.
- **Verification:** Unit tests `test_production_config_rejects_missing_app_db_url` and `test_production_config_rejects_default_dev_password` confirm fail-fast startup behavior.

### 3.3 Remediated: PII Eradication & Log Sanitization (CWE-532)
- **Problem:** `app/api/auth.py` logged plaintext user email addresses and client IP addresses on failed login attempts. In addition, the rate limiter stored plaintext email and IP strings in the database.
- **Remediation:**
  - Replaced all PII logging with correlation IDs (`cid:<uuid>`) and generic reason codes.
  - Implemented SHA-256 key hashing (`hash_rate_limit_key`) for email and IP identifiers in rate limiting.
  - Created `CorrelationIdFormatter` in `app/shared/logging.py` to prevent formatting crashes when foreign library loggers emit records without correlation context.
- **Verification:** Unit tests `test_hash_rate_limit_key_privacy` and `test_login_failure_logs_zero_pii` verify that neither logs nor rate limit tables contain sensitive information.

### 3.4 Remediated: XML Entity Expansion & SSRF Protection (CWE-611, CWE-827)
- **Problem:** Template linting and provenance modules parsed WordprocessingML files using `xml.etree.ElementTree`.
- **Remediation:** Migrated all XML parsing to `defusedxml.ElementTree as ET` across `split_runs.py`, `structural.py`, `fonts.py`, `tag_checker.py`, `leftover_scanner.py`, and `provenance.py`.
- **Verification:** Verified by `tests/unit/test_secure_xml.py` and Bandit security scanner.

---

## 4. Static Application Security Testing (SAST) Results

### 4.1 Bandit AST Security Analysis
Ran Bandit scanner against the entire `app` codebase:
```bash
bandit -r app -c pyproject.toml
```
- **High Severity Issues:** 0
- **Medium Severity Issues:** 0
- **Low Severity Issues:** Only standard informational notices (e.g. standard hashlib usage for non-cryptographic cache keys).
- **Result:** **PASSED**

### 4.2 Mypy Strict Type Analysis
Ran Mypy in strict mode across all 125 backend source files:
```bash
mypy -p app
```
- **Result:** `Success: no issues found in 125 source files`

### 4.3 Ruff Linter & Formatter
Ran Ruff across all backend files:
```bash
ruff check . && ruff format --check .
```
- **Result:** `All checks passed!` (217 files formatted cleanly)

---

## 5. Security Checklist Compliance (AGENTS.md & PRD)

- [x] **Zero Real Personal Data:** Only synthetic seed fixtures used; no external scraping.
- [x] **No eval/exec/pickle:** Safe condition DSL evaluated via AST Pratt parser.
- [x] **Approved Template Immutability:** Approved templates are immutable; versioning strictly forward.
- [x] **Zero Secrets in Code/Logs:** Passwords and API secrets supplied strictly via environment variables.
- [x] **Zero PII Logging:** Names, IDs, emails, IP addresses, and document contents excluded from logs.
- [x] **Backend-Enforced Authorization:** Every query scoped by `tenant_id` and authorized via `authorize(actor, action, resource)`.
- [x] **No Floats for Money/Area:** Exact `Decimal` and rational arithmetic enforced.
- [x] **Defused XML:** All DOCX XML parsing uses `defusedxml`.
- [x] **SameSite & Secure Cookies:** HTTP-only, Secure (in prod/staging), SameSite=Lax session cookies.
- [x] **Fail-Closed Architecture:** Database, RLS, and auth failures reject access closed.
