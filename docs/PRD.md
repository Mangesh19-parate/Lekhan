# PRD: Lekhan (working title), multilingual property legal drafting web app

**Version:** 1.0 (planning) | **Owner:** you (freelance product + engineering) | **Client:** the company (Nagpur/Vidarbha property documentation practice)
**Time box:** 26 weeks (6 months)
**Evidence base:** analysis of the company's 396 sample Word files (see "Corpus facts" below).

---

## 1. Problem

Document writers draft property deeds by opening an old, filled-in Word deed, finding and replacing party, property and money details, fixing Marathi/Hindi grammar by hand, then re-typing the same facts into a government registration portal.

Measured pain in the sample archive:
- **Legacy encoding:** 273 of 310 `.docx` files use Kruti Dev (non-Unicode), so text cannot be searched, reused or checked.
- **Leftover data risk:** 323 of 396 files are executed deeds with real client data; copying them risks carrying one client's data into another's document.
- **Hand-typed mechanics:** 61% have page numbers typed inline; 92% have numbering typed by hand.
- **Double entry:** the same party/property details are typed into the registration portal after drafting.

## 2. Vision

> Enter the facts of a transaction once; get a correct, editable, properly formatted Marathi or English deed (Hindi later), plus the data needed for registration, with a clear review trail.

## 3. Users

| Persona | Needs | Priority |
|---|---|---|
| **Drafter** (daily) | Fast entry, correct Marathi, reuse of parties, minimal clicks | P0 |
| **Advocate / reviewer** | Review drafts, see what changed, approve templates | P0 |
| **Template admin** (company lawyer; initially also you) | Version, review and approve templates | P0 |
| **Office owner/admin** | Users, backups, history, reports | P1 |

## 4. Goals and non-goals (6-month release)

### Goals
- G1. Generate correct, editable **Marathi and English** DOCX deeds for the **Wave 1** document set from one form.
- G2. Replace legacy Kruti Dev with Unicode, with a measured, reviewed conversion process.
- G3. Never carry another matter's data into a draft (leftover-data lint).
- G4. Keep an auditable record: template version, data snapshot, who generated, who reviewed.
- G5. Add a new template **without a code deployment**.
- G6. Produce a portal-ready party/property text from the same data (assistive; no automation of the portal).

### Non-goals in the 6 months
Hindi templates; Kruti Dev **export**; stamp-duty/registration-fee calculator (needs company-verified rules); duplicate-party detection; document comparison; multi-tenant SaaS operation; AI drafting; offline mode; e-signature; client portal; native mobile apps.

## 5. Scope (MoSCoW)

| Priority | Item |
|---|---|
| **Must** | Auth + roles; wizard (language, property type, document); dynamic form from manifest; Wave 1 templates (about 10); Unicode templates with automatic page numbers/numbering; DOCX generation; amount in words (MR, EN); date and area helpers; per-template validation; template versions (immutable once approved); review workflow; document history and download; automatic document numbering; leftover-data lint; audit log; backups with restore test; synthetic-data test suite |
| **Should** | PDF export; party and property reuse; search; advisory missing-info alerts; portal data-entry sheet; template admin UI; TOTP MFA |
| **Could** | Wave 2 templates (release deed, family partition, possession letter, leave and licence); diff between template versions; zone-map index lookup |
| **Won't (this release)** | See non-goals |

## 6. Wave 1 document set (from corpus frequency)

| Language | Documents |
|---|---|
| Marathi | Sale Deed (plot in NIT/NMC layout, flat, shop, agricultural), Agreement to Sell (plot, flat), General Power of Attorney |
| English | Sale Deed (flat), Agreement to Sell (flat), General Power of Attorney |

About 10 templates; roughly 45% of sample volume. The set is confirmed with the company's monthly volumes in Gate 0.

## 7. Corpus facts that drive requirements

| Fact | Requirement it creates |
|---|---|
| 22% of files are Hindi, 55% Marathi, 20% English | Language-neutral architecture; Hindi after launch |
| Plot deeds are about two thirds of Marathi sale deeds | Plot (NIT/NMC layout) is the first template |
| Fields: Mouza, PH No., Khasra, Plot, Sheet/City Survey No., ready-reckoner division and rate, four boundaries, Hectare-R | Vidarbha-first field dictionary |
| 48% contain amount in words; 35% contain instalment/payment lines | Amount-in-words engine; instalment repeater |
| 77% contain witnesses; 69% four boundaries | Repeating witness block; four-direction boundary block |
| Typed page numbers and numbering | Automatic page-number fields and generated numbering |
| 51% Legal-size pages, 18 pt Kruti | Page setup preserved; font size re-tuned for Unicode; pagination sign-off |

## 8. Functional requirements

IDs map to `FEATURES.md`.

| ID | Requirement | Acceptance (summary) |
|---|---|---|
| FR-01 | Authentication and roles (admin, template_admin, reviewer, drafter) | Backend-enforced; 403 tests pass for every role/action pair |
| FR-02 | Wizard: language, property type, document type | Only combinations with an **Approved** template are selectable |
| FR-03 | Manifest-driven form with repeaters (parties, instalments, witnesses, boundaries, multiple properties) | Fields and visibility change per template; min/max enforced; autosave |
| FR-04 | Per-language storage of names/addresses | Required scripts depend on document language; transliteration is suggestion only |
| FR-05 | Template engine: fill the company's real DOCX; conditional clauses; repeating rows | Golden-file tests; opens in Word without repair prompt; original template never modified |
| FR-06 | Unicode conversion toolchain (Kruti Dev to Unicode) | Round-trip score tracked; reviewer sign-off per template; no auto-approval |
| FR-07 | Leftover-data lint | Template or draft containing data from another matter is flagged |
| FR-08 | Amount in words (MR/EN), date and number formatting, area conversions | Property and known-value tests signed off by the company |
| FR-09 | Template lifecycle: Draft, Under review, Approved, Retired; immutable versions | Illegal transitions impossible; approver recorded |
| FR-10 | Review workflow for documents: Draft, Reviewed, Finalised | Disclaimer shown; "valid" wording never used |
| FR-11 | Document history and download; data snapshot stored | Past documents unchanged by later party edits |
| FR-12 | Automatic document numbering (gap-free per tenant per year) | 50 parallel creators produce 1..50 with no gaps or duplicates |
| FR-13 | PDF export | DOCX is master; PDF labelled convenience copy |
| FR-14 | Party/property reuse and search | Select prior party; trigram search works in Marathi |
| FR-15 | Advisory alerts (lawyer-authored rules) | Non-blocking, recorded in audit |
| FR-16 | Portal data-entry sheet | Text in the company's agreed format from the same data |
| FR-17 | Audit log | Create, edit, generate, download, approve events with actor and template version |
| FR-18 | Backups and restore | Daily backup; restore drill passed before go-live |

## 9. Non-functional requirements

| Area | Target |
|---|---|
| Performance | DOCX generation p95 under 3 s; PDF p95 under 10 s; page loads under 2 s |
| Reliability | 99.5% availability in working hours; failed generations under 1% and retryable |
| Security | HTTPS; argon2id; server-side sessions; RBAC on backend; field encryption for ID numbers; no PII in logs |
| Privacy | Minimal retention; ID numbers masked or encrypted; synthetic data only in dev and CI |
| Compatibility | Current Chrome and Edge; output opens in Microsoft Word 2016+ |
| Accessibility | WCAG 2.2 AA target |
| Localisation | UI in English and Marathi; documents in Marathi and English |

## 10. Success metrics (baselines set in Phase 0)

| Metric | Target |
|---|---|
| Time to first draft (Wave 1 documents) | At least 50% lower than current, measured on 10 real matters |
| Corrections per draft (lawyer review) | Falling across pilot weeks; target under 5 per draft by week 4 |
| Share of company volume covered by Wave 1 | About 45% at launch |
| Weekly active drafters after 4 weeks | At least 70% of pilot users |
| Failed generations | Under 1% |

## 11. Assumptions
1. The company provides redacted sample deeds and approves template wording.
2. A named lawyer signs off every template and Marathi grammar combination, with about 4-6 hours per week available.
3. Typists accept Unicode editing, **or** the company later pays for a Kruti Dev export (Gate 0 decision).
4. You work about 35-40 hours a week for 26 weeks. At half-time, scope halves (see PLAN.md).
5. One tenant (the company) at launch; schema is multi-tenant-ready.

## 12. Dependencies
Redacted samples and approvals from the company; licensed Kruti Dev font if previews of originals are needed; hosting account in an Indian region; domain name and email sender.

## 13. Risks (top)
Kruti conversion errors in signed deeds; leftover client data; layout change after font switch; template volume; legal liability; PII exposure. Full list in `ARCHITECTURE.md` section 12 and `PLAN.md` section 7.

## 14. Release criteria (Launch, end of week 26)
- All **Must** items complete and tested; Wave 1 templates **Approved** by the lawyer and in golden tests.
- Pilot drafters produced real drafts for at least 4 weeks with a falling correction count.
- Security checklist (AUTH.md) and restore drill passed.
- Documentation (README, SETUP, DEBUGGING) lets a second developer run and fix the system.

## 15. Open questions (blockers marked)
1. **(Blocker, Gate 0)** Do typists need to edit generated files in Kruti Dev?
2. **(Blocker)** Which sample deeds are approved precedents, and who owns wording decisions?
3. Monthly volumes by document and language (confirms Wave 1 and Hindi timing).
4. Registration portal data-entry routine and exact text format.
5. Hosting preference and data-residency rules.
6. Who owns code and templates; maintenance arrangement after launch.
7. Are the zone-map PDFs needed in v1, and what is their source and licence?

---

*Planning document. Not legal advice; the company's qualified professionals approve all legal wording, fees and rules.*
