# PLAN.md: 26-week delivery plan

**Reality check first.** Six months delivers a **safe, useful pilot-to-launch product** (Wave 1, Marathi + English, about 10 templates), not "every document in three languages". The remaining library is gated by the company's lawyers and takes a year or more. Anyone promising the full scope in six months is guessing.

**Assumptions:** about 35-40 working hours a week; one developer (you) using Antigravity agents; company lawyer available 4-6 hours a week; redacted samples already provided.
**Calendar (if Week 1 starts Monday 16 Nov 2026):** Week 13 ends Sun 14 Feb 2027; Week 26 ends **Sun 16 May 2027**. Adjust for holidays and exams; the buffer weeks are explicit below.

---

## 1. Phases and gates

| Phase | Weeks | Outcome | Gate |
|---|---|---|---|
| 0. Decisions and spike | 1-3 | Company decisions; converter prototype; one Marathi plot Sale Deed generated end to end | **Gate 0** (end W2): encoding, fonts, Wave 1 set, lawyer owner. **Gate 1** (end W3): lawyer approves spike output in Word |
| 1. Foundation | 4-7 | Repo, CI, auth, entities, template registry, generation jobs, audit | One document through the UI |
| 2. Template platform and factory | 8-13 | DSL, compiler, lint, form engine, language packs, hardened converter, leftover scanner, slot discovery | Converter score and lint thresholds agreed |
| 3. Wave 1 pilot | 14-19 | About 10 templates approved; review workflow; PDF; numbering; backups | **Gate 2** (end W19): real drafters produce real drafts |
| 4. Productivity | 20-23 | Party/property reuse, search, alerts, portal sheet, template admin UI, MFA | Adoption target met |
| 5. Hardening and launch | 24-26 | Security review, restore drill, load test, docs, training, go-live | **Launch** |

Template content work (curation, lawyer review) runs **in parallel from week 8**; it is the critical path.

---

## 2. Week by week

| Week | Goal | Deliverables / exit check |
|---|---|---|
| 1 | Kick-off and decisions | Send security notice and question list; sign Phase 0 agreement and NDA; repo + CI skeleton; run `npx getdesign@latest add starbucks`; Antigravity set up with `AGENTS.md` |
| 2 | **Gate 0** decisions; converter v0 | Written answers: Kruti vs Unicode editing, font choice, Wave 1 set, approver. Converter prototype runs on 20 Marathi files with run-aware conversion |
| 3 | **Gate 1** spike; skeleton checkpoint | One Marathi plot Sale Deed (1-4 parties, instalments, boundaries, witnesses, auto page numbers) as DOCX in Word. **Skeleton checkpoint:** login + one CRUD form + one generation call; if not working, switch to Django (ARCHITECTURE.md section 1) |
| 4 | Backend core | FastAPI app, config, DB, Alembic, health, logging with correlation ID, import-linter |
| 5 | Auth and tenancy | Sessions, argon2id, roles, CSRF, throttling; authorisation matrix tests |
| 6 | Entities | Parties (per-language), properties, matters, versions; optimistic locking; audit table |
| 7 | Template registry and jobs | Immutable template versions, object store port, jobs table with SKIP LOCKED worker, generation FSM v0. **Milestone:** doc generated through the UI |
| 8 | DSL | Tokenizer, Pratt parser, AST evaluator, conformance vectors, property tests |
| 9 | Compiler and DAG | Manifest schema v1, type-check, Kahn ordering, cycle rejection; manifest examples |
| 10 | DOCX lint + leftover scanner | Split-run merge, undefined tags, structural safety, leftover-data detection |
| 11 | Language packs | Marathi and English numbers-in-words (inverse-parser tests), dates, honorifics, join names, units |
| 12 | Form engine (frontend) | Schema-driven forms, repeaters, live amount-in-words, i18n (en, mr), design tokens from `DESIGN.md` |
| 13 | **Buffer** + converter hardening | Round-trip score on all Kruti files; review queue; catch-up. Phase 2 review with company |
| 14 | Wave 1 templates 1-3 | Marathi plot Sale Deed, Marathi plot Agreement to Sell, English flat Sale Deed (lawyer review starts) |
| 15 | Wave 1 templates 4-6 | Marathi flat and shop Sale Deed, Marathi General POA |
| 16 | Wave 1 templates 7-10 + review workflow | Remaining templates; document review FSM; disclaimers; template lifecycle UI (basic) |
| 17 | PDF + numbering + history | LibreOffice isolation, timeouts; gap-free numbering test (50 parallel); history list and download |
| 18 | Backups + observability + parity | Backup and restore script, Sentry, metrics; parity images for Wave 1 |
| 19 | **Gate 2** pilot start | 2-3 drafters use it on live matters; corrections log; bugfix window |
| 20 | Party/property reuse and search | Trigram search in Marathi; reuse with versioning |
| 21 | Alerts and portal sheet | Lawyer-authored advisory rules; portal data-entry text (format confirmed first) |
| 22 | Template admin UI + MFA | Upload, lint report view, approve flow; TOTP |
| 23 | **Buffer** + pilot feedback | Fix top corrections; usability fixes; Wave 2 template starts if ahead |
| 24 | Security and compliance | Threat-model walkthrough, dependency audit, ZAP baseline, IDOR tests, retention and purge jobs |
| 25 | Performance and recovery | k6 load test, failure drills (kill converter, fill disk), **restore drill** |
| 26 | Launch | Docs complete, training session, go-live checklist, handover; rollback plan |

---

## 3. Cut lines (what moves out if you are late)

Cut in this order, never cut tests, security, or the lawyer sign-off:
1. Portal data-entry sheet
2. TOTP MFA (keep strong passwords and throttling)
3. Template admin UI (use CLI plus manual approval)
4. Search polish (keep basic list filters)
5. PDF export (keep DOCX only)
6. Wave 1 templates 8-10

**Never cut:** auth and authorisation tests, leftover-data lint, immutable template versions, audit log, backups and restore drill, disclaimers, synthetic-data discipline.

## 4. If you are working half-time (about 20 hours a week)

| Scope | Result by week 26 |
|---|---|
| Phases 0-2 complete | Yes |
| Wave 1 | About 4-5 templates (Marathi plot Sale Deed, plot Agreement to Sell, English flat Sale Deed, General POA) |
| Phase 4 | Reuse and basic search only |
| Launch | Slides to about week 36-40 |
Tell the company this on day one; do not discover it in week 20.

---

## 5. Rituals
- **Daily:** 15-minute plan, write down one decision or surprise in `docs/journal.md` (source of your future interview stories).
- **Weekly (Friday):** 10-minute demo and written update to the company: done, next, risks, decisions needed. Update this plan's status column.
- **Fortnightly:** lawyer review session; template status board (Draft, Under review, Approved).
- **Per task:** plan with the agent, small change, tests, run lint, explain-back note (AGENTS.md), commit.

## 6. Definition of done (per task)
Code merged only when: tests written and passing; type checks and lint clean; no real personal data in repo or fixtures; docs updated if behaviour changed; you can explain the change in your own words; for templates: lint clean, golden tests, grammar combinations reviewed, lawyer approval recorded.

## 7. Risks to the schedule

| Risk | Early signal | Response |
|---|---|---|
| Lawyer review slower than plan | More than 3 templates waiting over a week | Reduce Wave 1; escalate; prefer fewer, better templates |
| Kruti conversion worse than expected | Round-trip score flat for two weeks | Narrow to subset; add manual correction tool; ask company for Unicode source text for key deeds |
| Skeleton checkpoint fails (W3) | No generation call by Friday | Switch to Django + HTMX; keep domain code |
| Scope creep | New document types mid-sprint | Change request with date impact in writing |
| Samples or decisions late | Gate 0 slips | Move dates, tell the company the new end date |
| Burnout / part-time reality | Two weeks under target hours | Apply half-time table immediately |
| PII incident | Real data found in repo or logs | Stop, rotate secrets, purge history, notify company |

## 8. Dependencies on the company

| Needed | By |
|---|---|
| Gate 0 answers (Kruti editing, approver, Wave 1 set, volumes) | End W2 |
| Lawyer owner and weekly hours | W2 |
| Lawyer review of spike | W3 |
| Marathi grammar combination sign-off tables | W11 onward |
| Pilot users (2-3 drafters) | W19 |
| Portal data-entry format (if portal sheet stays in scope) | W20 |
| Hosting account and domain | W17 |

## 9. Budget of effort (rough, 38 h/week)
Platform and application about 45%; template factory and converter about 25%; testing and quality about 15%; ops and security about 10%; communication about 5%. If template curation takes over 35%, cut platform polish, not templates.
