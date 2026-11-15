# RUNBOOK: Lekhan Operations, Deployment & Troubleshooting

> **Target Audience:** Developers, SREs, and system maintainers operating Lekhan.  
> **Acceptance Criterion (F-075):** A second developer can run, test, deploy, and fix the service independently.

---

## 1. Quick Start & Local Development

### 1.1 Prerequisites
- Python 3.12+
- Node.js 20+ (with npm)
- Docker & Docker Compose (for PostgreSQL dev database)
- LibreOffice (optional, for offline PDF rendering)

### 1.2 Setup Commands
```bash
# 1. Clone repository and install dependencies
make setup

# 2. Start PostgreSQL container in background
make dev

# 3. Apply database migrations
make migrate

# 4. Populate synthetic development accounts & seed matters
make seed

# 5. Run full test suite & linters
make check
```

---

## 2. Release Engineering & Deployment

### 2.1 Separate Migration Release Step
In production and staging environments (Kubernetes, AWS ECS, Heroku, etc.), **database migrations must run as an isolated release phase before web replicas boot**. Never run `alembic upgrade head` in application container startup scripts or entrypoints to prevent race conditions, schema lock contention, and connection storms.

```bash
# Step 1: Pre-deployment migration runner (isolated one-off container or initContainer)
python -m alembic upgrade head

# Step 2: Once migration exits with code 0, roll application containers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2.2 Graceful Shutdown & Drain
The application registers a FastAPI `lifespan` handler that cleans up database connections on termination signals (`SIGTERM`, `SIGINT`).
- Container orchestrators should set a `terminationGracePeriodSeconds` of at least 30 seconds.
- Incoming requests finish processing; the connection pool drains and closes via `engine.dispose()`.

---

## 3. Database Administration & Pooling

### 3.1 Database Connection Pool Configuration
Database pool parameters are configurable via environment variables in `backend/app/config.py`:
- `DB_POOL_SIZE` (default: `10`): Number of persistent connections kept in the pool per worker process.
- `DB_MAX_OVERFLOW` (default: `20`): Max temporary connections allowed beyond pool size during traffic spikes.
- `DB_POOL_TIMEOUT` (default: `30`): Seconds to wait for an available connection before raising a 503 error.
- `DB_POOL_RECYCLE` (default: `3600`): Recycle connections older than 1 hour to prevent stale connection leaks.

*Total database connection sizing formula:*
$$\text{Max DB Connections} = \text{Web Replicas} \times \text{Workers Per Pod} \times (\text{DB\_POOL\_SIZE} + \text{DB\_MAX\_OVERFLOW}) + \text{Background Worker Connections}$$

Ensure PostgreSQL `max_connections` is tuned above this threshold with headroom for administrative access.

### 3.2 Automated Backup Drill & Verification
Logical backups are created via `pg_dump` with custom directory format (`-Fc`). Disaster recovery drills must be verified regularly using `backend/tests/integration/test_postgres_backup_restore.py`:

```bash
# 1. Create timestamped logical backup
pg_dump -Fc -h localhost -U lekhan_user lekhan_db > var/backups/backup_$(date +%Y%m%d_%H%M%S).dump

# 2. Verify integrity by restoring into isolated drill database
createdb -h localhost -U lekhan_user lekhan_drill_db
pg_restore -h localhost -U lekhan_user -d lekhan_drill_db --clean var/backups/backup_*.dump

# 3. Execute drill validation suite
pytest backend/tests/integration/test_postgres_backup_restore.py -q

# 4. Clean up drill database
dropdb -h localhost -U lekhan_user lekhan_drill_db
```

---

## 4. Security, Rate Limiting & Error Contract

### 4.1 Structured Error Contract (RFC 9457 `application/problem+json`)
All API errors adhere strictly to the RFC 9457 standard and return `Content-Type: application/problem+json`:

```json
{
  "type": "https://errors.lekhan.local/resource-not-found",
  "title": "Not Found",
  "status": 404,
  "code": "RESOURCE_NOT_FOUND",
  "detail": "Template draft-102 not found.",
  "correlation_id": "c7a840e1-0f2c-4029-8730-8d5f2a1b919d",
  "errors": []
}
```
Standard status code mappings:
- `400`: `BAD_REQUEST`
- `401`: `UNAUTHENTICATED`
- `403`: `FORBIDDEN` / `PERMISSION_DENIED`
- `404`: `NOT_FOUND`
- `413`: `REQUEST_ENTITY_TOO_LARGE` (exceeds `MAX_REQUEST_SIZE_BYTES`, default 10MB)
- `422`: `VALIDATION_ERROR` (with field-level validation errors list)
- `429`: `TOO_MANY_REQUESTS`
- `500`: `INTERNAL_ERROR`
- `503`: `SERVICE_UNAVAILABLE` (database pool exhaustion or offline DB)

### 4.2 Database-Backed Rate Limiting & Account Lockout
Rate limiting is backed by PostgreSQL via the `rate_limits` table (no process-local memory state), ensuring consistent enforcement across multiple load-balanced web replicas:
- **Login attempts:** 5 failures within 15 minutes trigger `429 Too Many Requests`.
- **Brute-force lockout:** 10 failures trigger `423 Locked` until administrative unlock or backoff expiration.
- **Atomic updates:** Updates use atomic SQL writes or row-level locking to avoid race conditions.

### 4.3 Request Size Limits
The `RequestSizeLimitMiddleware` inspects `Content-Length` and stream bytes:
- Any payload exceeding `MAX_REQUEST_SIZE_BYTES` (default 10 MB) is immediately aborted with HTTP 413 `application/problem+json`.
- Template uploads are separately restricted to a 5 MB maximum size with upfront magic byte MIME inspection.

---

## 5. Observability & Zero-PII Tracing

### 5.1 OpenTelemetry Distributed Tracing
Distributed tracing tracks requests via `OpenTelemetryTracingMiddleware`.
- Every span generates a W3C-compliant trace parent and unique `correlation_id`.
- **Strict Zero-PII Policy:** Telemetry attributes are whitelisted. The tracer explicitly drops all sensitive keys:
  - Allowed: `tenant_id`, `actor_id`, `correlation_id`, `http.method`, `http.route`, `http.status_code`, `duration_ms`.
  - Blocked & Stripped: `name`, `pan`, `aadhaar`, `phone`, `address`, `email`, `payload`, `password`, `content`.

### 5.2 Metrics & Health Probes
- `/health/live`: Probes process liveliness.
- `/health/ready`: Probes PostgreSQL connectivity. Returns `503 Service Unavailable` if the DB is unreachable.
- `/metrics`: Prometheus metrics endpoint protected by bearer token / network allowlist (`METRICS_AUTH_TOKEN`).

---

## 6. Performance Targets & Load Testing

### 6.1 Performance SLO / p95 Latency Targets
Under sustained load of 20 concurrent virtual users:
- **Read / Health endpoints (`/health/ready`):** p95 < 50ms
- **Query / Helper utilities (`/api/v1/helpers/*`):** p95 < 200ms
- **Document Generation / Preview (`/api/v1/matters/preview`):** p95 < 800ms
- **HTTP Error Rate:** < 1.0% (and 0% unexpected 500 errors)

### 6.2 Running Load Tests

#### Option A: k6 (Recommended)
```bash
# Run local baseline test (3 minutes, 20 VUs)
k6 run backend/tests/load/k6_load_test.js

# Run against staging environment
k6 run --env BASE_URL=https://staging.lekhan.local backend/tests/load/k6_load_test.js
```

#### Option B: Locust
```bash
# Run headless Locust benchmark
locust -f backend/tests/load/locustfile.py --headless -u 20 -r 2 -t 3m --host http://localhost:8000
```

---

## 7. Template Lifecycle & Approval Runbook

Per separation-of-duties rules, a template version submitter **cannot** approve their own template.

```
[ Author DOCX + Manifest ] 
       │
       ▼
[ Upload as 'draft' ] ────> [ Run DocxLinter ]
                                   │
                                   ▼
                            [ Submit for Review ]
                                   │ (Reviewer checks AST, grammar, tags)
                                   ▼
                            [ Approve Version ] ──> [ Becomes Immutable in DB ]
```

1. **Upload & Linting:**
   ```bash
   curl -X POST http://127.0.0.1:8000/api/v1/templates/{template_id}/lint \
     -H "Cookie: lekhan_session=..."
   ```
2. **Approval Verification:**
   Approved templates compute an SHA-256 hash stored in `template_versions`. Any attempt to update an approved version is rejected by database triggers.

---

## 8. Incident Response & Troubleshooting

### 8.1 Issue: `422 Unprocessable Entity` on Document Generation
- **Root Cause:** Schema mismatch in generation payload.
- **Verification:** Ensure the financial block is named `financial` (not `financial_details`) and includes `instalments: []`.
- **Log Inspection:** Search logs for `SpikeGenerationError` or Pydantic validation traceback with correlation ID (`X-Correlation-ID`).

### 8.2 Issue: `401 Unauthorized` on API Calls
- **Root Cause:** Session cookie expired, missing, or tenant mismatch.
- **Fix:** Re-authenticate via `POST /api/v1/auth/login` and ensure credentials pass `SameSite=Lax` headers.

### 8.3 Issue: PII Found in Application Logs
- **Action:**
  1. Immediately alert developer lead per AGENTS.md Rule 1.
  2. Identify correlation ID.
  3. Rotate Sentry and server secrets if leaked to external monitoring.
  4. Ensure all logging statements use `audit_service` or sanitized ID logging.

---

## 9. Cryptographic Key & Secret Rotation Procedures

All cryptographic keys in staging and production must be rotated periodically (minimum every 90 days) or immediately upon suspected compromise.

### 9.1 `SECRET_KEY` Rotation (Session Signing Key)

`SECRET_KEY` signs session cookies and HMAC audit trail exports. Rotating `SECRET_KEY` invalidates active user sessions, forcing re-authentication without data loss.

1. **Generate New Secret:**
   ```bash
   openssl rand -hex 32 > deploy/secrets/secret_key.secret.new
   ```
2. **Execute Staged Deployment:**
   - Deploy web replicas with the new key in `/run/secrets/secret_key`.
   - Active user sessions expire gracefully and re-login issues fresh cookies signed with the new key.
   - Record the rotation event in the audit trail:
     ```bash
     python -c "from app.audit.service import audit_service; import uuid; audit_service.log_event(tenant_id=uuid.UUID('00000000-0000-0000-0000-000000000000'), action='secret_key_rotated', entity='system_config')"
     ```
3. **Clean Up Old Secret:**
   - Overwrite old secret file securely (`shred -u deploy/secrets/secret_key.secret`).

---

### 9.2 `MASTER_KEY` Rotation (AES-256-GCM Field Encryption)

`MASTER_KEY` encrypts sensitive PII fields (Aadhaar, PAN, phone numbers) at rest using AES-GCM envelope encryption (`backend/app/adapters/crypto.py`).

1. **Generate New Master Key:**
   ```bash
   # Generate exactly 32 cryptographically secure bytes, base64 encoded
   openssl rand -base64 32 > deploy/secrets/master_key.secret.new
   ```
2. **Execute Re-encryption Migration:**
   Run the offline field re-encryption script against the database:
   ```bash
   python backend/scripts/rotate_master_key.py \
     --old-key-file deploy/secrets/master_key.secret \
     --new-key-file deploy/secrets/master_key.secret.new
   ```
   *The re-encryption script:*
   - Decrypts each encrypted ciphertext chunk with `OLD_MASTER_KEY`.
   - Generates a fresh 12-byte initialization vector (IV).
   - Re-encrypts with `NEW_MASTER_KEY` and updates the row atomically.
3. **Promote New Key & Restart Services:**
   ```bash
   mv deploy/secrets/master_key.secret.new deploy/secrets/master_key.secret
   docker compose -f docker-compose.prod.yml restart api worker
   ```

---

### 9.3 `INDEX_KEY` Rotation (HMAC Blind Indexing)

`INDEX_KEY` computes HMAC-SHA256 blind search hashes for encrypted fields (e.g., party lookup by PAN or phone without decrypting all table rows).

1. **Generate New Index Key:**
   ```bash
   openssl rand -base64 32 > deploy/secrets/index_key.secret.new
   ```
2. **Recompute Blind Index Hashes:**
   ```bash
   python backend/scripts/reindex_blind_hashes.py \
     --new-key-file deploy/secrets/index_key.secret.new
   ```
3. **Promote Key and Reload:**
   ```bash
   mv deploy/secrets/index_key.secret.new deploy/secrets/index_key.secret
   docker compose -f docker-compose.prod.yml restart api worker
   ```

---

### 9.4 PostgreSQL Database Password Rotation

1. Connect to PostgreSQL as superuser/owner and update the user password:
   ```sql
   ALTER USER lekhan WITH PASSWORD 'NEW_STRONG_PASSWORD_32_CHARS';
   ```
2. Update the Docker secret:
   ```bash
   echo -n 'NEW_STRONG_PASSWORD_32_CHARS' > deploy/secrets/db_password.secret
   ```
3. Restart API and Worker services sequentially to pick up the new secret file:
   ```bash
   docker compose -f docker-compose.prod.yml restart api
   docker compose -f docker-compose.prod.yml restart worker
   ```

---

## 10. Security Incident Response Playbooks

### 10.1 Playbook A: Cryptographic Key Compromise or Leak

- **Severity:** P0 (Critical)
- **Trigger:** Secret file accidentally committed, exposed in container logs, or leaked via unauthorized access.
- **Immediate Containment (Within 15 minutes):**
  1. Revoke the leaked secret immediately by generating a fresh key per Section 9.
  2. If `SECRET_KEY` leaked: Invalidate all active sessions across all tenants in PostgreSQL:
     ```sql
     DELETE FROM sessions;
     ```
  3. If `MASTER_KEY` leaked: Immediately initiate re-encryption using a new key.
  4. Redploy all containers using `docker compose -f docker-compose.prod.yml up -d --force-recreate`.
  5. Check git history and git reflog; rewrite git history if secret was committed before pushing remote.

---

### 10.2 Playbook B: Audit Chain Broken / Tamper Alert (`AUDIT_CHAIN_INTEGRITY_ALERT`)

- **Severity:** P0 (Critical / Legal Integrity)
- **Trigger:** Nightly job or `GET /api/v1/admin/audit/verify` returns `tamper_detected: true` or logs `AUDIT_CHAIN_INTEGRITY_ALERT`.
- **Investigation & Isolation (Within 30 minutes):**
  1. **Identify Affected Tenant:** Inspect log correlation ID and tenant ID reported in the alert:
     ```bash
     docker logs lekhan_api_prod | grep -E "AUDIT_CHAIN_INTEGRITY_ALERT"
     ```
  2. **Locate Break Point:** Run the chain inspector to locate the exact record ID where `prev_hash != computed_hash`:
     ```bash
     python -c "from app.audit.service import audit_service; import uuid; print(audit_service.verify_audit_chain(uuid.UUID('<TENANT_ID>')))"
     ```
  3. **Export Current Evidence:**
     Pull the signed audit export and export the raw database rows before any database writes:
     ```bash
     curl -s -H "Cookie: lekhan_session=..." https://lekhan.local/api/v1/admin/audit/export > audit_evidence_$(date +%s).json
     ```
  4. **Forensic Database Inspection:**
     Check PostgreSQL `pg_stat_statements` or database audit logs for direct manual `UPDATE` or `DELETE` statements executed outside the application.
  5. **Escalate to Legal & Compliance:**
     Document the break point, timestamp, and affected document IDs. Do not overwrite or delete audit rows.

---

### 10.3 Playbook C: Disaster Recovery & Scratch DB Restore Verification

- **Severity:** P1 (Disaster Recovery)
- **Trigger:** Database server failure, storage volume corruption, or ransomware disaster.
- **Recovery Procedure:**
  1. Locate the latest verified daily backup archive from secure offsite backup storage (`var/backups/backup_*.tar.gz`).
  2. Verify the SHA-256 checksum of the archive before extracting:
     ```bash
     sha256sum -c backup_YYYYMMDD_HHMMSS.tar.gz.sha256
     ```
  3. Spin up an isolated scratch PostgreSQL instance:
     ```bash
     docker run -d --name lekhan_scratch_drill -e POSTGRES_PASSWORD=drill_pass -e POSTGRES_DB=lekhan_scratch postgres:16-alpine
     ```
  4. Execute automated restore into the scratch database:
     ```bash
     python backend/scripts/restore.py /path/to/backup.tar.gz --target-storage /var/storage_restored
     ```
  5. Run the cryptographic verification drill:
     ```bash
     python backend/scripts/restore_drill.py
     ```
  6. Verify that `audit_chain_verified: true` and all gap-free counters match pre-disaster state.

---

### 10.4 Playbook D: PII Leak in Logs or External APM

- **Severity:** P1 (Data Privacy Violation)
- **Trigger:** Real party names, Aadhaar, PAN numbers, or document text spotted in logs.
- **Remediation Steps:**
  1. Alert the technical lead immediately per AGENTS.md Hard Rule 1 & Rule 5.
  2. Identify the origin log statement, endpoint, or middleware that logged the payload.
  3. Purge APM / CloudWatch / Sentry log streams containing the correlation ID.
  4. Patch the offending logging call: ensure it logs only entity IDs and correlation IDs, never input dictionaries or model dumps.
  5. Run `make check` and the security scan gate to ensure zero regressions.

---

### 10.5 Playbook E: Distributed Denial of Service (DDoS) / Brute-Force Attacks

- **Severity:** P2 (Operational Service Degradation)
- **Trigger:** Spike in `429 Too Many Requests` or `423 Locked` responses in Caddy access logs.
- **Action Plan:**
  1. Check rate-limiting table status in PostgreSQL:
     ```sql
     SELECT key, consecutive_failures, locked_until FROM rate_limits WHERE consecutive_failures > 5;
     ```
  2. Identify attacking IP blocks in Caddy access logs:
     ```bash
     docker logs lekhan_caddy_prod | grep -E '"status":429|"status":423' | jq -r .request.remote_ip | sort | uniq -c | sort -nr | head -20
     ```
  3. Block abusive IP blocks at Caddy or edge firewall / Cloudflare:
     ```caddy
     @blocked remote_ip <ABUSIVE_IP_CIDR>
     respond @blocked 403
     ```
  4. Confirm application replicas are healthy via `/health/ready` and latency has normalized.
