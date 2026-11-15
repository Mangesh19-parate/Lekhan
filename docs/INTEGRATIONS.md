# INTEGRATIONS.md

Every external dependency sits behind a **port** (a Python `Protocol`) with an adapter in `backend/app/adapters/`. The domain never imports vendor SDKs. Each integration has a fake adapter for tests.

---

## 1. Summary

| Integration | Port | Phase | Required for launch | Failure behaviour |
|---|---|---|---|---|
| PostgreSQL | repositories | W4 | Yes | App not ready; `/health/ready` fails |
| Object storage (local volume, later S3-compatible) | `ObjectStore` | W7 | Yes | Generation job fails retryable; downloads `503` |
| DOCX renderer (docxtpl) | `DocxRenderer` | W3 | Yes | Job fails terminal with lint-style error |
| PDF converter (LibreOffice, optional Gotenberg) | `PdfConverter` | W17 | Should | DOCX still delivered; PDF marked unavailable |
| Email (SMTP) | `Mailer` | W5 | Yes (password reset) | Queue and retry; user sees neutral message |
| Error tracking (Sentry) | logging handler | W18 | Yes | Never blocks requests |
| Backups (pg_dump + object sync) | `BackupTarget` | W18 | Yes | Alert if no successful backup in 26 hours |
| Fonts | files on server and desktops | W3 | Yes | Lint warns on missing fonts |
| Registration portal | **export only** (`PortalSheetExporter`) | W21 | Should | Not applicable |
| Zone-map library | `ReferenceIndex` | Later | No | Feature hidden |
| AI assistant | `AiPort` | Later | No | Feature off by default |
| Hosting, DNS, TLS (Caddy) | n/a | W17 | Yes | n/a |
| CI/CD (GitHub Actions) | n/a | W1 | Yes | Blocks merges |

---

## 2. Details

### 2.1 LibreOffice (PDF) and Gotenberg
- Used only to convert **generated DOCX to PDF**. Never used to edit templates.
- Direct subprocess: `soffice --headless --convert-to pdf --outdir <tmp> <file>` with a unique `-env:UserInstallation=file:///tmp/lo_<uuid>` profile, hard timeout (for example 60 s), kill the process group on timeout, clean up in `finally`, semaphore for concurrency (default 2).
- Optional **Gotenberg** container behind the same port when you want a managed queue and isolation.
- Fonts must exist on the server or layout will shift. DOCX is the master; PDF is labelled a convenience copy.
- Security: run as non-root, read-only filesystem except temp dir, no network access for the converter container.

### 2.2 Object storage
- v1: a mounted volume with content-addressed keys (`templates/<sha256>.docx`, `documents/<output_hash>.docx`).
- Later: S3-compatible (AWS S3 in an Indian region, or MinIO) with private buckets, server-side encryption, signed URLs (60 s).
- Interface: `put(key, bytes)`, `get(key)`, `exists(key)`, `signed_url(key, ttl, user_id)`; writes are atomic.

### 2.3 Email (SMTP)
Used for password reset and (optionally) review notifications. Provider-agnostic SMTP settings via `SMTP_*` env vars. Never include document content or personal data in emails. SPF, DKIM and DMARC configured on the sending domain.

### 2.4 Sentry (or equivalent)
Scrub personal data before sending: no request bodies, no document text, no names; keep correlation ids and stack traces. `send_default_pii=False`. Separate projects for staging and production.

### 2.5 Backups
Nightly `pg_dump -Fc`, plus object-store sync, encrypted (for example with `age` or `restic`), stored off the server. Weekly automated restore into a scratch database with a smoke test. Retention: 14 daily, 8 weekly. Alert on failure or age.

### 2.6 Fonts
- Choose one open Devanagari font for templates (recorded in ADR-014) and install it on the server and on desktops.
- Kruti Dev: only the company's **licensed** copy, used for previews of original files and for the later export. Do not copy font files from third-party repositories.
- Mangal: Microsoft font; check licensing before bundling on a Linux server.

### 2.7 Registration portal (assistive only)
The drafter currently retypes party and property details into a government registration portal. Lekhan **generates text in the portal's entry pattern** so the drafter can copy and paste it. It does **not** log in, scrape, automate, or submit anything on the portal. Rationale: terms of use, fragility, and legal accountability. Confirm the exact format and field list with the company before building; version the format so portal changes are a small edit.

### 2.8 Zone-map library (reference)
139 large PDFs plus an index (sheet number to villages) built from file names. Store outside the main repo; index in `reference_zone_sheets`. Confirm source and licence with the company before distributing inside the product. v1 does not embed the PDFs.

### 2.9 Typing aids for Marathi
Rely on the operating system's Marathi keyboards and the browser's input method in v1. Offer a **transliteration suggestion** (Latin to Devanagari) as an optional local feature later, with the user confirming the result. Do not depend on third-party typing APIs in the core path, and do not send client text to external services.

### 2.10 Optional AI assist (Later)
Off by default, per-tenant switch, explicit per-use consent recorded in audit. Pipeline: detect personal data, replace with placeholders, send, re-insert locally; log categories sent, not content. Prefer a locally hosted model for privacy. No core workflow may depend on it.

### 2.11 Hosting and operations
- India-region VM (for example AWS Mumbai or a Bengaluru provider). Docker Compose, Caddy for TLS, firewall allowing only 80/443 and SSH from your IP, automatic security updates.
- DNS with short TTL during launch; staging environment mirrors production with synthetic data.
- Secrets: environment variables from a root-only file or the provider's secret manager; never in git.

### 2.12 CI/CD
GitHub Actions: lint, type-check, tests, import-linter, golden-file tests, OpenAPI diff, container build, vulnerability scan, deploy to staging on merge, manual approval to production. Dependabot or Renovate for updates; pin and review.

---

## 3. Environment variables (reference)

| Variable | Purpose |
|---|---|
| `ENV` | `dev`, `staging`, `prod` |
| `DATABASE_URL` | Application DB (non-owner role) |
| `SECRET_KEY` | Session/CSRF signing |
| `MASTER_KEY` | Envelope-encryption master key (base64) |
| `INDEX_KEY` | HMAC key for blind indexes |
| `STORAGE_PATH` or `S3_ENDPOINT`, `S3_BUCKET`, `S3_ACCESS_KEY`, `S3_SECRET_KEY` | Object storage |
| `SOFFICE_BIN` or `GOTENBERG_URL` | PDF converter |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Email |
| `SENTRY_DSN` | Error tracking |
| `ALLOWED_ORIGINS` | CORS |
| `SESSION_IDLE_MINUTES`, `SESSION_ABSOLUTE_HOURS` | Session policy |

A committed `.env.example` lists names only, never values.

## 4. Integration testing
Each port has a contract test run against both the fake and the real adapter: put/get/exists for storage; render of a known template for DOCX; conversion of a known DOCX within the timeout for PDF; mail delivery to a local SMTP sink. Failure tests simulate timeouts, disk full and unavailable services, and assert the documented failure behaviour.
