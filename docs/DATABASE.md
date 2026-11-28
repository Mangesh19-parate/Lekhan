# DATABASE.md

PostgreSQL 16. SQLAlchemy 2.0 models, Alembic migrations. **Synthetic data only** in dev, CI and test fixtures.

---

## 1. Conventions
- Every table: `id uuid PRIMARY KEY` (UUIDv7 generated in application code, time-ordered), `tenant_id uuid NOT NULL`, `created_at timestamptz NOT NULL DEFAULT now()`, `updated_at timestamptz`.
- Money: `numeric(18,2)`. Never `float`.
- Timestamps in UTC; formatting per language at render time.
- Soft delete via `deleted_at`; hard delete only by a reviewed purge job.
- Mutable business rows carry `version integer NOT NULL DEFAULT 1` for optimistic locking.
- JSONB only where the shape legitimately varies (manifest, property attributes, data snapshot); validate it with Pydantic on write.
- Enums as `text` + `CHECK` (easier to migrate than native enums).

Extensions: `pg_trgm`, `btree_gist`, `pgcrypto` (only for hashing helpers; encryption of ID numbers is done in the application).

---

## 2. Entity overview

```
tenants --< users --< sessions
tenants --< parties --< party_versions
tenants --< properties
tenants --< matters --< matter_parties >-- parties
                    \--< documents >-- template_versions >-- templates
documents --< jobs          documents --< document_reviews
tenants --< counters        tenants --< audit_log (hash chain)
fee_rules (global or tenant)    reference_zone_sheets (global)
```

---

## 3. Core DDL

```sql
CREATE TABLE tenants (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  settings jsonb NOT NULL DEFAULT '{}',
  feature_flags jsonb NOT NULL DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  email citext_or_text NOT NULL,           -- store lower-cased; unique per tenant
  display_name text NOT NULL,
  password_hash text NOT NULL,             -- argon2id
  role text NOT NULL CHECK (role IN ('admin','template_admin','reviewer','drafter')),
  ui_language text NOT NULL DEFAULT 'en' CHECK (ui_language IN ('en','mr','hi')),
  mfa_secret_enc bytea,
  active boolean NOT NULL DEFAULT true,
  failed_logins integer NOT NULL DEFAULT 0,
  locked_until timestamptz,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, email)
);

CREATE TABLE sessions (
  id_hash bytea PRIMARY KEY,               -- SHA-256 of the opaque cookie value
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  tenant_id uuid NOT NULL,
  csrf_token_hash bytea NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  last_seen_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  user_agent text, ip inet
);

-- PARTIES: names and addresses stored per language, never auto-transliterated.
CREATE TABLE parties (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  kind text NOT NULL CHECK (kind IN ('individual','company','firm','society')),
  gender text CHECK (gender IN ('male','female','other')),
  marital_status text,
  age_or_dob jsonb,                        -- {"age":42} or {"dob":"1982-03-01"}
  names jsonb NOT NULL,                    -- {"mr":{"full":"..","father":".."},"en":{...}}
  occupations jsonb NOT NULL DEFAULT '{}',
  addresses jsonb NOT NULL DEFAULT '{}',
  contact_enc bytea,                       -- mobile/email, envelope-encrypted
  pan_enc bytea, pan_blind_index bytea,    -- ciphertext + HMAC for equality search
  id_type text, id_enc bytea, id_blind_index bytea,   -- Aadhaar etc. (retention rules apply)
  version integer NOT NULL DEFAULT 1,
  deleted_at timestamptz,
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz
);

CREATE TABLE party_versions (
  party_id uuid NOT NULL REFERENCES parties(id),
  version integer NOT NULL,
  data jsonb NOT NULL,
  changed_by uuid REFERENCES users(id),
  changed_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (party_id, version)
);

CREATE TABLE properties (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  category text NOT NULL CHECK (category IN ('plot','flat','shop','agri','house_on_plot')),
  attrs jsonb NOT NULL,                    -- mouza, ph_no, khasra, plot_no, sheet_no, city_survey_no, ...
  area_value numeric(18,4),
  area_unit text CHECK (area_unit IN ('sqm','sqft','hectare_r','guntha','acre')),
  boundaries jsonb,                        -- {"east":"..","west":"..","north":"..","south":".."}
  rr_division text, rr_rate numeric(18,2), -- ready-reckoner division and rate (as entered, not computed)
  version integer NOT NULL DEFAULT 1,
  deleted_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE matters (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  matter_no text NOT NULL,
  title text,
  status text NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
  assigned_to uuid REFERENCES users(id),
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, matter_no)
);

CREATE TABLE matter_parties (
  matter_id uuid NOT NULL REFERENCES matters(id) ON DELETE CASCADE,
  party_id uuid NOT NULL REFERENCES parties(id),
  role text NOT NULL,                      -- seller, buyer, executant, attorney, witness, ...
  PRIMARY KEY (matter_id, party_id, role)
);

-- TEMPLATES: immutable once approved.
CREATE TABLE templates (
  id uuid PRIMARY KEY,
  tenant_id uuid,                          -- NULL = platform library
  doc_type text NOT NULL,                  -- sale_deed, agreement_to_sell, general_poa, ...
  property_category text,                  -- plot, flat, shop, agri, NULL if not applicable
  language text NOT NULL CHECK (language IN ('mr','en','hi')),
  name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, doc_type, property_category, language, name)
);

CREATE TABLE template_versions (
  id uuid PRIMARY KEY,
  template_id uuid NOT NULL REFERENCES templates(id),
  version integer NOT NULL,
  manifest_schema integer NOT NULL,
  manifest jsonb NOT NULL,
  compiled_ref text,                       -- object-store key of the compiled artifact
  file_ref text NOT NULL,                  -- object-store key of the DOCX
  file_sha256 bytea NOT NULL,
  lint_report jsonb,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','under_review','approved','retired')),
  approved_by uuid REFERENCES users(id),
  approved_at timestamptz,
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (template_id, version),
  CHECK (status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE documents (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL REFERENCES tenants(id),
  matter_id uuid REFERENCES matters(id),
  template_version_id uuid NOT NULL REFERENCES template_versions(id),
  engine_version text NOT NULL,
  language text NOT NULL,
  doc_no text,                             -- gap-free numbering
  data_snapshot jsonb,                     -- excludes 'ephemeral' fields
  data_snapshot_enc bytea,                 -- optional encrypted variant
  input_hash bytea, output_hash bytea,
  docx_ref text, pdf_ref text,
  status text NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','reviewed','finalised')),
  version integer NOT NULL DEFAULT 1,
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, doc_no)
);

CREATE TABLE document_reviews (
  id uuid PRIMARY KEY,
  document_id uuid NOT NULL REFERENCES documents(id),
  tenant_id uuid NOT NULL,
  reviewer_id uuid NOT NULL REFERENCES users(id),
  decision text NOT NULL CHECK (decision IN ('reviewed','finalised','changes_requested')),
  checklist jsonb, comment text,
  at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
  id uuid PRIMARY KEY,
  tenant_id uuid NOT NULL,
  type text NOT NULL,                      -- generate_docx, convert_pdf, backup_check, ...
  payload jsonb NOT NULL,
  status text NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','running','succeeded','failed','dead')),
  state text,                              -- pipeline state (REQUESTED..COMPLETED)
  run_at timestamptz NOT NULL DEFAULT now(),
  attempts integer NOT NULL DEFAULT 0,
  locked_at timestamptz,
  idempotency_key text,
  error jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, idempotency_key)
);

CREATE TABLE counters (
  tenant_id uuid NOT NULL,
  key text NOT NULL,
  year integer NOT NULL,
  value integer NOT NULL,
  PRIMARY KEY (tenant_id, key, year)
);

CREATE EXTENSION IF NOT EXISTS btree_gist;
CREATE TABLE fee_rules (
  id uuid PRIMARY KEY,
  tenant_id uuid,                          -- NULL = global
  doc_type text NOT NULL,
  jurisdiction text NOT NULL,
  rule jsonb NOT NULL,                     -- DSL AST + slabs
  validity daterange NOT NULL,
  source_ref text NOT NULL,                -- official source, mandatory
  verified_by text NOT NULL,
  EXCLUDE USING gist (doc_type WITH =, jurisdiction WITH =, validity WITH &&)
);

CREATE TABLE audit_log (
  id bigserial PRIMARY KEY,
  tenant_id uuid NOT NULL,
  actor_id uuid,
  action text NOT NULL,
  entity text NOT NULL,
  entity_id text,
  at timestamptz NOT NULL DEFAULT now(),
  meta jsonb NOT NULL DEFAULT '{}',
  prev_hash bytea, hash bytea NOT NULL
);

CREATE TABLE reference_zone_sheets (
  sheet_no integer PRIMARY KEY,
  villages text[] NOT NULL,
  file_ref text NOT NULL,
  source_note text
);
```

(`citext_or_text` above: use `citext` with the `citext` extension, or `text` with a lower-cased unique index. Pick one and record it in an ADR.)

---

## 4. Indexes

```sql
CREATE INDEX idx_parties_name_mr_trgm ON parties USING gin ((names->'mr'->>'full') gin_trgm_ops);
CREATE INDEX idx_parties_name_en_trgm ON parties USING gin ((names->'en'->>'full') gin_trgm_ops);
CREATE INDEX idx_parties_pan_bidx ON parties (tenant_id, pan_blind_index) WHERE pan_blind_index IS NOT NULL;
CREATE INDEX idx_properties_attrs ON properties USING gin (attrs jsonb_path_ops);
CREATE INDEX idx_documents_matter ON documents (tenant_id, matter_id, created_at DESC);
CREATE INDEX idx_documents_tv ON documents (template_version_id);
CREATE INDEX idx_jobs_queue ON jobs (run_at) WHERE status = 'queued';
CREATE INDEX idx_audit_entity ON audit_log (tenant_id, entity, entity_id, at DESC);
CREATE INDEX idx_sessions_user ON sessions (user_id);
```

Devanagari has no useful stemmer in Postgres full-text; use trigram search for names and addresses.

---

## 5. Critical SQL patterns

**Gap-free numbering (same transaction as the document insert):**
```sql
INSERT INTO counters (tenant_id, key, year, value) VALUES ($1, $2, $3, 1)
ON CONFLICT (tenant_id, key, year) DO UPDATE SET value = counters.value + 1
RETURNING value;
```

**Job claim without Redis:**
```sql
UPDATE jobs SET status='running', locked_at=now(), attempts=attempts+1
WHERE id = (
  SELECT id FROM jobs WHERE status='queued' AND run_at <= now()
  ORDER BY run_at FOR UPDATE SKIP LOCKED LIMIT 1)
RETURNING *;
```
A janitor job requeues `running` jobs whose `locked_at` is older than the timeout.

**Audit hash chain:** `hash = SHA256(prev_hash || canonical_json(row_without_hash))`, computed inside the same transaction under an advisory lock per tenant. A nightly job verifies the chain and alerts on mismatch.

---

## 6. Immutability and integrity
- Approved template versions: block UPDATE/DELETE with a trigger (`RAISE EXCEPTION` when `OLD.status='approved'` except for `status` changing to `retired`).
- `audit_log`: grant the app role INSERT and SELECT only (no UPDATE/DELETE).
- Content-addressed object keys: `templates/<sha256>.docx`, `documents/<output_hash>.docx`.

---

## 7. Row-Level Security (design now, enable before a second tenant)

```sql
ALTER TABLE parties ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON parties
  USING (tenant_id = current_setting('app.tenant_id')::uuid);
-- per request: SET LOCAL app.tenant_id = '<uuid>';
```
Apply the same policy to every tenant-scoped table. The application role must **not** be the table owner (owners bypass RLS unless `FORCE ROW LEVEL SECURITY`).

---

## 8. Sensitive data and retention

| Class | Behaviour | Example |
|---|---|---|
| `ephemeral` | Held only in an encrypted draft with TTL; excluded from `data_snapshot`; generated file still contains it | Full Aadhaar/PAN when a template requires it |
| `matter` | Kept while matter is open; purged by schedule | Witness phone numbers |
| `permanent` | Kept for reuse | Names, addresses |

Envelope encryption: per-tenant data key encrypted by a master key (`MASTER_KEY`), AES-256-GCM, key id stored with ciphertext to support rotation. Blind index = `HMAC(index_key, normalised_value)`.

---

## 9. Migrations
- Alembic, one migration per PR, reviewed; **expand/contract** for breaking changes (add nullable, backfill, switch code, then drop).
- Every migration has a tested downgrade or a documented "forward-only" note.
- CI runs migrations on an empty database and on a database loaded with the previous release's synthetic fixture.
- Never edit an applied migration.

## 10. Seeds (synthetic only)
`backend/scripts/seed_dev.py` creates one tenant, one user per role, 20 fake parties (Marathi and English names), 10 fake properties, and Wave 1 templates marked `approved` **in dev only**. Production never runs the seed script.

## 11. Backups
Nightly `pg_dump` (custom format) plus object-store sync, encrypted, shipped off-server; weekly restore into a scratch database with an automated smoke query; keep 14 dailies and 8 weeklies. RPO 24 h, RTO 4 h.

## 12. Performance notes
`EXPLAIN (ANALYZE, BUFFERS)` for any query over 100 ms in staging; avoid `SELECT *` on JSONB-heavy tables; paginate with cursors (`(created_at, id)`); partition `documents` and `audit_log` by month only when row counts justify it (trigger in ARCHITECTURE.md section 11).

---

## 13. Production Least-Privilege & Row-Level Security Enforcement

### 13.1 Database Roles Architecture
1. **Migration / Admin Role (`DATABASE_URL`)**:
   - Table owner; executes Alembic migrations during isolated release steps.
   - Holds full DDL (`CREATE`, `ALTER`, `DROP`) permissions.
   - Never exposed to web application pods in production environments.
2. **Application Runtime Role (`APP_DATABASE_URL`, `lekhan_app`)**:
   - Connects the FastAPI application and background worker processes.
   - Restricted to DML operations (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) on runtime tables.
   - Granted `USAGE, SELECT` on all sequences.
   - Strictly forbidden from `DROP`, `TRUNCATE`, or `ALTER TABLE`.
   - `NOBYPASSRLS` enforced: subject to all PostgreSQL Row-Level Security policies.
   - Append-only tables like `audit_log` permit only `INSERT` and `SELECT`; runtime role cannot `UPDATE` or `DELETE` audit entries.

### 13.2 Migration 0015: Forward-Only Role Password Synchronization
- Created as forward-only migration `backend/migrations/versions/0015_harden_app_role_password.py`.
- Synchronizes `lekhan_app` role password with the secret environment variable `LEKHAN_APP_PASSWORD` or `APP_DATABASE_URL`.
- Enforces fail-fast behavior: if `ENVIRONMENT in ('staging', 'production')` and `LEKHAN_APP_PASSWORD` is unset or contains default development passwords (`lekhan_app_dev_password`, `change-me`), migration immediately aborts deployment.
- Never alters historical applied migrations `0001` through `0014`.

### 13.3 Fail-Closed Tenant Context Protocol
- In `app/adapters/db.py:set_tenant_context()`:
  ```sql
  SET LOCAL app.current_tenant_id = :tenant_id
  ```
- **Fail-Closed Execution**: If executing `SET LOCAL` raises any database or syntax error, the function raises immediately without masking. Unhandled tenant context errors trigger immediate session rollback.
- Context isolation is tracked via `ContextVar[uuid.UUID | None]` and reset using tokens in `finally:` blocks on every HTTP request and background worker job.
- When `current_tenant_id` is unset or null, RLS policies evaluate to false, rendering tenant-scoped records completely invisible to the session.
