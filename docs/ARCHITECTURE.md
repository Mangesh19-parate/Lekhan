# ARCHITECTURE.md

Modular monolith, hexagonal (ports and adapters), config-driven templates. Built to be **correct first, scalable later**. Scaling steps have written triggers (section 11); nothing is distributed until a measurement says so.

---

## 1. Stack (decided)

| Layer | Choice |
|---|---|
| Frontend | React 18, TypeScript (strict), Vite, Tailwind (tokens from `DESIGN.md`), React Hook Form + Zod, TanStack Query, react-i18next |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 (`pg_trgm`, `btree_gist`, JSONB) |
| DOCX | `docxtpl` (python-docx + Jinja2, sandboxed) |
| PDF | LibreOffice headless (direct subprocess; Gotenberg sidecar optional) |
| Storage | Local volume first; S3-compatible later behind the same port |
| Auth | Server-side sessions in Postgres, HTTP-only cookies, argon2id |
| Jobs | Postgres queue (`FOR UPDATE SKIP LOCKED`), worker = same image, different command |
| Infra | Docker Compose, Caddy (HTTPS), GitHub Actions, Sentry |
| Tests | pytest, Hypothesis, Playwright, Schemathesis |

**Fallback decision (end of week 3):** if the React + FastAPI skeleton (login, one CRUD form, one generation call) is not working, switch to Django + HTMX. The domain layer is framework-free so that this swap costs days, not weeks.

---

## 2. Style and layers

```
Browser (React) --HTTPS/JSON--> API layer (FastAPI, thin)
                                     |
                         Application layer (use cases, transactions, authorisation)
                                     |
                         Domain layer (pure Python, no I/O)
                           catalog | parties | properties | matters
                           templates (manifest, DSL, compiler, lint)
                           lang_packs | units | review (FSM) | numbering
                                     |
                              ports (Protocols)
        Postgres repos | Object store | DOCX renderer | PDF converter | Clock/IDs/Crypto
```

Rules:
1. Domain code never imports FastAPI, SQLAlchemy, or file-system APIs.
2. No cross-module table access; modules talk through application services.
3. Boundaries enforced in CI with `import-linter`.
4. Cross-module notifications use in-process domain events; async work goes through the `jobs` table (outbox style).

### Modules

| Module | Owns |
|---|---|
| `identity` | users, sessions, roles, MFA |
| `tenancy` | tenants, settings, feature flags |
| `catalog` | document types, property types, applicability matrix |
| `parties`, `properties`, `matters` | entities, versions, matter grouping |
| `templates` | manifests, DSL, compiler, registry, lint |
| `generation` | pipeline, jobs, artifacts |
| `review` | lifecycle state machines |
| `lang_packs` | numbers, dates, digits, honorifics, grammar, encodings (Kruti) |
| `units` | exact area/length conversion |
| `search` | trigram search read models |
| `audit` | append-only log |
| `reference` | zone-map index (read-only) |

### Repository layout

```
lekhan/
  AGENTS.md  DESIGN.md  README.md
  backend/app/{shared,identity,tenancy,catalog,parties,properties,matters,
               templates,generation,review,lang_packs,units,search,audit,reference,adapters}/
  backend/migrations/  backend/tests/{unit,property,golden,api,e2e}/
  frontend/src/{features,shared}/
  corpus_tools/            # offline CLI used by the developer, not shipped to users
  templates-library/       # approved DOCX + manifests (synthetic or redacted only)
  conformance/             # shared DSL test vectors
  docs/  deploy/
```

---

## 3. Template platform (the core)

**Template = DOCX file + manifest.** The form, validation, conditions and derived fields come from the manifest.

### 3.1 Layers
1. **Manifest** (declarative; `manifest_schema: N`): parties, repeaters, sections, fields, conditions, validations, derived fields, retention classes, language, property type, digits setting.
2. **Compiler** (on publish): validate, parse conditions to AST, type-check, build the field dependency graph, lint the DOCX, emit an immutable compiled artifact.
3. **Runtime** (per generation): validate, compute derived fields in dependency order, build context via language pack, render, post-process, verify.
4. **Language packs**: numbers, dates, digits, honorifics, plural and verb forms, name joining.

### 3.2 Condition DSL (no `eval`, ever)
Closed vocabulary: `eq ne gt gte lt lte and or not in contains is_empty`, plus `count any all` over repeaters. Stored as JSON AST, compiled from a readable syntax by a tokenizer + Pratt parser. No loops, recursion, function definitions or attribute access; evaluation is O(AST size) with depth and node limits. Two evaluators later (Python authoritative, TypeScript for UX) share `conformance/` vectors; until then the UI calls `POST /validate`.

```json
{"op":"and","args":[
  {"op":"eq","args":[{"var":"financial.payment_mode"},{"lit":"bank_loan"}]},
  {"op":"gt","args":[{"var":"financial.loan_amount"},{"lit":0}]}
]}
```

### 3.3 Dependency graph
Visibility, requiredness and derived fields (`balance = total - advance`, area conversions) form a DAG. Kahn's algorithm orders evaluation and **rejects cycles at publish time**.

### 3.4 DOCX lint (blocks approval)
1. Split-run tags: tags must sit inside one run (auto-merge runs with identical formatting).
2. Undefined tags and unused manifest fields.
3. **Leftover data**: names, 12-digit IDs, PAN patterns, phone numbers, plot/khasra numbers, dates and amounts that look like real data.
4. Structural safety: reject macros (`.docm`), strip external relationships, size and decompression-ratio limits, `defusedxml` parsing.
5. Font report: fonts used versus fonts installed on server and recommended for desktops.

### 3.5 Rendering sandbox
`docxtpl` renders with Jinja `SandboxedEnvironment` and a whitelist of filters/macros supplied by language packs.

### 3.6 Language pack interface
```python
class LanguagePack(Protocol):
    code: str
    def number_to_words(self, n: Decimal, *, currency: bool) -> str: ...
    def format_date(self, d: date, style: str) -> str: ...
    def to_digits(self, s: str) -> str: ...
    def honorific(self, party: PartyView) -> str: ...
    def join_names(self, names: list[str]) -> str: ...
    def verb(self, base: str, parties: list[PartyView], tense: str) -> str: ...
    def plural(self, parties: list[PartyView]) -> bool: ...
```
Marathi and Hindi grammar tables are owned and signed off by the company's lawyers. Code is the lookup engine.

---

## 4. Encoding architecture (Kruti Dev)

**Facts:** 273 of 310 `.docx` samples use Kruti Dev variants (010, 021, 030, 050, 100, 111, DevLys). Latin text sits in other fonts.

**Decision (Gate 0 confirms):** Unicode is canonical for data and templates. A Kruti Dev **export** is a later optional adapter. Kruti-native storage is rejected.

### 4.1 Converter requirements (`lang_packs/encodings`, `corpus_tools`)
1. Run-aware: convert only runs whose font is Kruti/DevLys.
2. Merge adjacent same-format runs before converting (conjuncts and matra reordering must not cross run boundaries); warn on mid-word formatting boundaries.
3. Per-variant mapping tables, verified with test strings.
4. Reordering: pre-base i-matra, reph, half forms, nukta, chandrabindu/anusvara, ZWJ/ZWNJ, Marathi letters (retroflex L, eyelash reph).
5. Detect Latin typed under a Kruti font (PAN, Aadhaar, cheque numbers, amounts) and queue for review.
6. **Corpus regression:** round-trip (Kruti to Unicode to Kruti) over all Kruti files; the score is tracked per release; leftovers go to a human review queue.
7. Output is a **draft**; a Marathi-literate reviewer signs off each template.

An open-source mapping table was used only for analysis. It left roughly 219 dangling half-letters and 154 stray combining marks across 308 files, so it is not production-grade. Own and test the converter; check licences before reusing anyone's table. Do not copy font files from third-party repositories.

### 4.2 Fonts
Choose one open Devanagari font for templates and install it on the server and desktops (recommended), or keep Mangal with a documented PDF caveat. Decision recorded in an ADR at Gate 1. Mangal is a Microsoft font; check licensing before bundling it on Linux.

---

## 5. Generation pipeline

```
REQUESTED -> VALIDATED -> RENDERED -> (CONVERTED) -> VERIFIED -> STORED -> COMPLETED
    \___________\__________\_____________\____________\__________/-> FAILED (retryable | terminal)
```

- Each transition persisted; a crash resumes from the last state.
- **Idempotency:** client sends `Idempotency-Key`; unique key on `jobs`; handlers write to a path derived from `output_hash`.
- **Optimistic locking** (`version` column) on parties, properties, documents.
- **Atomic file writes:** temp file, `fsync`, `rename`.
- **Verification gate:** ZIP integrity and python-docx reopen; **no leftover `{{`, `}}`, `{%`, `%}`** in any XML part; required fields non-empty; page count within template range; deterministic core properties so identical input gives identical bytes.
- **LibreOffice isolation:** unique `-env:UserInstallation` profile per conversion, hard timeout, kill the process group, clean temp directory, semaphore on concurrency.
- Retry with backoff and jitter for infrastructure failures; terminal failure for validation errors; dead-letter state with admin retry.

---

## 6. Formatting policy (preserve the look, fix the mechanics)

| Aspect | Policy |
|---|---|
| Page size, margins, alignment, bold/underline conventions | Preserve (Legal size where the template uses it) |
| Font and size | Unicode font; size re-tuned (Kruti 18 pt is roughly 12-14 pt in Noto/Mangal); pagination re-approved |
| Typed page numbers (".... 2 ....") | Replace with automatic PAGE fields |
| Typed numbering ("1)", "2)") | Generate from repeaters/lists |
| Tabs/dots layout | Rebuild with tab stops or small tables where it improves stability, with before/after sign-off |
| Signature and witness blocks | "Keep with next" to avoid orphaned signatures |

**Parity test:** render original (licensed Kruti font) and new template to images; compare line breaks and page counts per clause; record accepted deviations per template.

---

## 7. Data and tenancy (summary; full DDL in DATABASE.md)

- `tenant_id` on every table from day one; UUIDv7 ids generated in application code.
- Documents carry a **data snapshot**, never live references, plus `template_version_id`, `engine_version`, `input_hash`, `output_hash`.
- RLS designed now, enabled before a second tenant exists.
- Retention classes per field: `ephemeral`, `matter`, `permanent`.
- Envelope encryption for ID numbers; blind index (HMAC) for equality search.

---

## 8. Algorithms in use (only where a requirement needs them)

| Requirement | Technique |
|---|---|
| Conditions | Pratt parser, AST, tree-walk evaluator |
| Field dependencies | DAG, Kahn topological sort, cycle detection |
| Amount in words | Indian-grouping decomposition, 0-99 tables, `Decimal`; inverse parser as test oracle |
| Money and area | `Decimal` / exact rationals; no floats |
| Fee-rule lookup | Postgres `daterange` + GiST exclusion constraint |
| Workflow | Finite state machine with guards |
| Audit integrity | Hash chain (`SHA256(prev || canonical_json)`) |
| Numbering | Counter row updated in the same transaction (gap-free) |
| Queue | `FOR UPDATE SKIP LOCKED` |
| Name search | `pg_trgm` + GIN |
| Slot discovery (developer tool) | Paragraph alignment (LCS/Myers) across similar deeds |
| Unicode safety | Grapheme clusters (`\X`), NFC normalisation |

---

## 9. Security architecture (summary; details in AUTH.md)
STRIDE-driven. Every query is tenant-scoped **and** authorised by a policy function; opaque IDs are never the control. Signed short-lived download URLs; CSRF protection for cookie sessions; upload limits; sandboxed template rendering; no PII in logs; encrypted off-server backups with restore drills.

---

## 10. Observability
Structured JSON logs with correlation IDs carried into jobs; metrics (generation duration, queue depth/age, failure rate per template version, conversion timeouts); alerts for missing backup, audit-chain mismatch, failure spike, disk usage; Sentry for errors.

---

## 11. Scaling stages and triggers

| Stage | Topology | Move on when |
|---|---|---|
| A (launch) | One VM: Caddy, API, worker, Postgres, local volume, nightly backup | PDF queue wait p95 over 30 s, or a second tenant signs |
| B | Managed Postgres, S3-compatible storage, 2 API instances, separate render workers, RLS on | DB CPU over 60% sustained, or about 50 tenants |
| C | Read replica, monthly partitions for `documents` and `audit_log`, autoscaled workers | Evidence from metrics only |

Capacity sanity check: one company, 10 users, 150 documents a day is trivial (DOCX about 0.3 s, PDF about 3 s). At 1,000 users and 15,000 documents a day you need roughly 8 concurrent PDF conversions. The render worker is the first and probably only service that is ever extracted.

---

## 12. Risks (architecture-level)

| Risk | Mitigation |
|---|---|
| Kruti conversion errors reach a signed deed | Round-trip tests, review queue, lawyer sign-off, no auto-approval |
| Leftover client data | Lint as release blocker plus user-facing warning |
| Layout shift after font change | Parity images and pagination sign-off |
| Split-run tags (median 1,038 runs per file; max 20,703) | Mandatory run merging in lint and in conversion |
| Word vs PDF mismatch | DOCX is master; font strategy; PDF labelled convenience |
| Template explosion | Canonical templates, clause library, waves |
| Single developer | Docs, tests, deploy scripts, handover guide |

---

## 13. Architecture decision records (to write in `docs/adr/`)

| ADR | Decision |
|---|---|
| 001 | Modular monolith, hexagonal |
| 002 | Postgres queue, no Redis |
| 003 | Declarative DSL + AST evaluator |
| 004 | docxtpl on real company DOCX |
| 005 | Snapshot data in documents |
| 006 | `tenant_id` now, RLS later |
| 007 | Server-side sessions with HTTP-only cookies |
| 008 | Names and addresses stored per language |
| 009 | Retention classes for identifiers |
| 010 | DOCX master, PDF convenience |
| 011 | Decimal and rationals for money and area |
| 012 | Gap-free counter in same transaction |
| 013 | Unicode canonical; Kruti export optional |
| 014 | Font choice for templates |

Each ADR: Context, Options, Decision, Consequences, **How we will know we were wrong**.
