# FEATURES.md

Status key: `[ ]` not started, `[~]` in progress, `[x]` done. Priority: **M** must, **S** should, **C** could, **W** won't (this 6-month release). Release: **Spike** (W3), **Pilot** (W19), **Launch** (W26), **Later**.

Requirement IDs (FR-xx) link to `PRD.md`.

---

## A. Platform and access

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-001 | Login/logout, server-side sessions | M | Pilot | FR-01 | [x] | Cookie flags, CSRF, rotation tested |
| F-002 | Roles and `authorize()` policy | M | Pilot | FR-01 | [x] | Matrix test: every endpoint x role |
| F-003 | User management (admin) | M | Pilot | FR-01 | [x] | Temporary password, forced change |
| F-004 | Login throttling and lockout | M | Pilot | FR-01 | [x] | `429`/`423` thresholds tested |
| F-005 | TOTP MFA | S | Launch | FR-01 | [x] | Enrol, verify, recovery codes |
| F-006 | Tenant settings (digits, numbering format, retention) | M | Pilot | FR-12 | [x] | Changes audited |
| F-007 | Audit log + hash-chain verification | M | Pilot | FR-17 | [x] | Tamper test detects a changed row |

## B. Wizard and forms

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-010 | Wizard: language, property type, document type | M | Pilot | FR-02 | [x] | Only Approved templates selectable |
| F-011 | Manifest-driven dynamic form | M | Pilot | FR-03 | [x] | Fields change per template and property type |
| F-012 | Repeaters: parties, instalments, witnesses, boundaries, multiple properties | M | Pilot | FR-03 | [x] | Min/max, renumbering, undo on remove |
| F-013 | Per-language name/address entry; transliteration suggestion | M | Pilot | FR-04 | [x] | Suggestion never saved without confirmation (transliterate.ts) |
| F-014 | Live amount in words (MR, EN) | M | Pilot | FR-08 | [x] | Inverse-parser property test |
| F-015 | Input masks (amounts with Indian grouping, dates, PAN, pincode) | M | Pilot | FR-03 | [x] | Keyboard-only entry works (masks.ts) |
| F-016 | Autosave drafts | M | Pilot | FR-03 | [x] | Refresh does not lose data; local drafts drawer + autosave engine |
| F-017 | Server-side validation endpoint with derived fields | M | Pilot | FR-03 | [x] | Same rules as generation |
| F-018 | UI in English and Marathi | M | Launch | FR-04 | [x] | No layout break with Marathi strings |
| F-019 | Hindi UI | W | Later | n/a | n/a | Pack interface only |

## C. Template platform

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-020 | Manifest schema v1 + versioning | M | Spike-Pilot | FR-05 | [x] | `manifest_schema` stored with each version |
| F-021 | Condition DSL (tokenizer, Pratt parser, AST evaluator) | M | Pilot | FR-05 | [x] | Conformance vectors; mutation score tracked |
| F-022 | Field dependency graph (Kahn), cycle rejection | M | Pilot | FR-05 | [x] | Cyclic template cannot publish |
| F-023 | DOCX lint: split runs, undefined tags, safety checks | M | Pilot | FR-05 | [x] | Blocks approval on error |
| F-024 | Leftover-data lint (templates and drafts) | M | Pilot | FR-07 | [x] | Detects names, IDs, PAN, phones, plot/khasra numbers |
| F-025 | Sandboxed rendering (Jinja SandboxedEnvironment) | M | Pilot | FR-05 | [x] | Escape attempts fail in tests |
| F-026 | Template lifecycle FSM (Draft, Under review, Approved, Retired) | M | Pilot | FR-09 | [x] | Submitter cannot approve |
| F-027 | Immutable approved versions (DB trigger + hash) | M | Pilot | FR-09 | [x] | UPDATE rejected |
| F-028 | Template admin UI (upload, lint report, approve) | S | Launch | FR-09 | [x] | CLI fallback exists |
| F-029 | Clause library (reusable blocks) | S | Launch | FR-05 | [x] | Instalment, bank-loan, witness, TDS blocks (clauses.py) |
| F-030 | Diff between template versions | C | Later | FR-09 | [x] | Paragraph then word level, grapheme-aware (diff.py) |

## D. Language and encoding

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-040 | Language pack interface (numbers, dates, digits, honorifics, verbs, join, plural) | M | Pilot | FR-08 | [x] | Marathi and English implemented |
| F-041 | Marathi number-to-words with 0-99 table, lakh/crore | M | Pilot | FR-08 | [x] | Company signs off 200 sample amounts |
| F-042 | Gender/number agreement helpers | M | Pilot | FR-05 | [x] | 1M, 1F, 2M, mixed, 3+ combinations reviewed |
| F-043 | Area and unit conversion (sqft, sqm, hectare-R, guntha) | M | Pilot | FR-08 | [x] | Exact constants agreed with the company |
| F-044 | Kruti/DevLys to Unicode converter (run-aware, merged runs) | M | Pilot | FR-06 | [x] | Round-trip score tracked; review queue |
| F-045 | Latin-typed-in-Kruti detector | M | Pilot | FR-06 | [x] | PAN/IDs/amounts flagged |
| F-046 | Unicode to Kruti export | W | Later | n/a | [ ] | Only if Gate 0 requires |
| F-047 | Hindi templates and pack | W | Later | n/a | [x] | Hindi language pack with numbers, dates, honorifics (hindi.py) |

## E. Generation and documents

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-050 | DOCX generation from approved template | M | Spike-Pilot | FR-05 | [x] | Opens in Word without repair; golden tests |
| F-051 | Generation pipeline FSM, idempotency, atomic writes | M | Pilot | FR-05 | [x] | Double submit yields one document |
| F-052 | Verification gate (no leftover tags, reopen, page range) | M | Pilot | FR-05 | [x] | Fails closed |
| F-053 | Automatic page-number fields and generated numbering | M | Pilot | FR-05 | [x] | Replaces typed numbers; lawyer sign-off |
| F-054 | Data snapshot + `engine_version` + hashes | M | Pilot | FR-11 | [x] | Regenerate reproduces output |
| F-055 | Gap-free document numbering | M | Pilot | FR-12 | [x] | 50-parallel test |
| F-056 | PDF export via LibreOffice (isolated, timeout) | S | Launch | FR-13 | [x] | DOCX stays master |
| F-057 | Document history, filters, download (signed URL) | M | Pilot | FR-11 | [x] | Cross-tenant `404` |
| F-058 | Document review workflow (Draft, Reviewed, Finalised) + checklist | M | Pilot | FR-10 | [x] | Disclaimer always visible |
| F-059 | Regenerate with newer template version (explicit) | C | Launch | FR-11 | [ ] | Shows differences |

## F. Productivity and reference

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-060 | Party and property reuse with versions | S | Launch | FR-14 | [x] | Past documents unchanged |
| F-061 | Trigram search in Marathi and English | S | Launch | FR-14 | [x] | GIN index used (EXPLAIN) |
| F-062 | Advisory missing-info alerts (lawyer-authored rules) | S | Launch | FR-15 | [x] | Non-blocking, audited |
| F-063 | Portal data-entry sheet | S | Launch | FR-16 | [x] | Format confirmed with company first |
| F-064 | Zone-map sheet lookup (village to sheet number) | C | Later | n/a | [x] | Nagpur Mouza to sheet index (zone_map.py) |
| F-065 | Duplicate-party detection | W | Later | n/a | [x] | Exact PAN and trigram similarity (detect_duplicates) |
| F-066 | Document comparison | W | Later | n/a | [x] | Myers diff, grapheme-aware (diff.py) |
| F-067 | Stamp duty and registration-fee calculator | W | Later | n/a | [x] | Maharashtra Stamp Act Sched I Art 25 (stamp_duty.py) |

## G. Operations and quality

| ID | Feature | Pri | Release | PRD | Status | Acceptance note |
|---|---|---|---|---|---|---|
| F-070 | Backups with weekly automated restore test | M | Launch | FR-18 | [x] | Restore drill signed off |
| F-071 | Observability: logs, metrics, Sentry, alerts | M | Launch | n/a | [x] | Correlation ids end to end |
| F-072 | CI pipeline (lint, types, tests, import-linter, golden, schema diff) | M | Pilot | n/a | [x] | GitHub Actions workflow (.github/workflows/ci.yml) |
| F-073 | Load and failure drills | M | Launch | n/a | [ ] | SLOs in ARCHITECTURE.md met |
| F-074 | Synthetic dev data and seed | M | Pilot | n/a | [x] | No real data anywhere |
| F-075 | Handover docs and runbooks | M | Launch | n/a | [x] | Comprehensive operations runbook (RUNBOOK.md) |
| F-080 | Enterprise navigation shell (19 items across 4 operational domains) | M | Launch | PRD | [x] | Zero placeholder routes; collapsible sidebar with token adherence |
| F-081 | Real-time operational dashboard & KPI metrics | M | Launch | PRD | [x] | Real backend stats, language breakdown, audit chain timeline |
| F-082 | 3-panel dynamic drafting workspace with live AST calculations | M | Launch | PRD | [x] | Form stepper, dynamic repeaters, instant preview, backend autosave |
| F-083 | Deterministic document quality inspection & DocxLinter | M | Launch | PRD | [x] | Tag verification, leftover detector, OpenXML dimensions, balance check |
| F-084 | Review & statutory approval center with checklist enforcement | M | Launch | PRD | [x] | Separation of duties, statutory disclaimer, immutable finalization |
| F-085 | Enterprise administration, RBAC permissions, & telemetry | M | Launch | PRD | [x] | SHA-256 chain verification, user roster, connection pool health |

## H. Wave 1 templates (content)

| ID | Template | Language | Status |
|---|---|---|---|
| T-01 | Sale Deed, plot (NIT/NMC layout) | MR | [x] |
| T-02 | Agreement to Sell, plot | MR | [x] |
| T-03 | Sale Deed, flat | EN | [x] |
| T-04 | Sale Deed, flat | MR | [x] |
| T-05 | Sale Deed, shop | MR | [x] |
| T-06 | Sale Deed, agricultural (Mouza/Khasra/Hectare-R) | MR | [x] |
| T-07 | Agreement to Sell, flat | MR | [x] |
| T-08 | Agreement to Sell, flat | EN | [x] |
| T-09 | General Power of Attorney | MR | [x] |
| T-10 | General Power of Attorney | EN | [x] |

Each template is done only when: lint clean, leftover scan clean, grammar combinations reviewed, golden tests pass, parity images accepted, lawyer approval recorded.

## I. Later backlog (after launch)
Wave 2 (release/hakkasod, family partition, possession, leave and licence, mortgage, partnership, will, consent/hamipatra); Hindi; Kruti export; fee calculator; duplicate detection; document comparison; multi-tenant operation with RLS; optional AI assist with redaction; product-side MCP server; Gotenberg and S3 scale-out.

## J. Explicitly not planned
E-signature, client portal, payment collection, direct automation of government portals (assistive export only), mobile apps.
