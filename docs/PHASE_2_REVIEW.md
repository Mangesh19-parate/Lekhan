# Phase 2 Review & Milestone Sign-Off

**Date:** November 2026  
**Milestone:** Phase 2 (Weeks 8–13) — Template Platform and Factory  
**Status:** **APPROVED & COMPLETED**  
**Audience:** Company Legal Team, Engineering Leadership, Antigravity Agent  

---

## 1. Executive Summary

Phase 2 focused on delivering the automated template platform, condition DSL, compiler DAG, DOCX linting, regional language packs, schema-driven form engine, and hardened Kruti-to-Unicode conversion toolchain.

All deliverables for Weeks 8 through 13 have been executed, verified, and integrated into the core application.

---

## 2. Weekly Deliverables Scorecard

| Week | Planned Goal | Status | Key Deliverable |
|---|---|---|---|
| **8** | Condition DSL | **Done** | Tokenizer, Pratt parser, AST evaluator, `conformance/dsl.json` shared test vectors (zero `eval`, O(N) complexity). |
| **9** | Compiler & DAG | **Done** | Manifest Schema v1, type-check, Kahn topological sort, cycle rejection, immutable `CompiledManifest`. |
| **10** | DOCX Lint + Leftover Scanner | **Done** | Split-run auto-merger, undefined tag blocker, structural safety (zip-bomb/macro checks), PII leftover scanner. |
| **11** | Language Packs | **Done** | Marathi and English numbers-in-words (0-99 table, Lakh, Crore), inverse-parser test oracles, Devanagari digit converters. |
| **12** | Form Engine | **Done** | React dynamic forms, repeaters with min/max, live amount-in-words, bilingual i18n (`en.json`, `mr.json`), `DESIGN.md` tokens. |
| **13** | Buffer + Converter Hardening | **Done** | Round-trip scorer, Latin-in-Kruti detector, human `ReviewQueue`, corpus regression benchmark. |

---

## 3. Agreed Quality & Governance Thresholds

In accordance with Phase 2 exit criteria, the following formal thresholds are agreed with the company:

### 3.1 Converter Fidelity Threshold
- **Benchmark Target:** $\ge 98.0\%$ round-trip character similarity on legal deeds.
- **Review Queue Trigger:** Any candidate template scoring $< 98.0\%$ or containing flagged Latin fragments (PAN, cheque numbers, amounts) is automatically enqueued in `corpus_tools/review_queue.py` and requires human advocate sign-off before entering the template library.
- **Auto-Approval Policy:** Strictly **prohibited** per FR-06. Every approved template version requires human review.

### 3.2 Template Lint Threshold
- **Zero Errors Allowed:** A template cannot be submitted or approved if it contains any of the following:
  1. Undefined tags (`UNDEFINED_TAG`)
  2. Legacy Kruti/DevLys fonts (`LEGACY_FONT_KRUTI_FOUND`)
  3. Macro-enabled files (`MACRO_ENABLED_FILE`)
  4. Decompression ratio $> 100:1$ or file size $> 5\text{ MB}$
  5. Prohibited external relationships (`TargetMode="External"`)
- **Zero Leftover Data:** Any detected real-world PAN, Aadhaar, phone number, IFSC, or untagged amount unconditionally blocks approval (`can_approve = False`).

### 3.3 Security & Authorisation
- **Separation of Duties:** Submitter/creator of a template version cannot approve their own template.
- **Tenant Isolation:** Cross-tenant resource queries return `404 NOT FOUND`.

---

## 4. Phase 3 (Wave 1 Pilot) Readiness

Phase 2 platform components are stable and operational. The codebase is unlocked and approved to proceed with **Phase 3 (Weeks 14–19)**:
- **Week 14:** Wave 1 Templates 1–3 (Marathi Plot Sale Deed, Marathi Plot Agreement to Sell, English Flat Sale Deed).
- **Week 15:** Wave 1 Templates 4–6 (Marathi Flat & Shop Sale Deed, General POA).
- **Week 16:** Wave 1 Templates 7–10 and Document Review FSM.
- **Week 17:** PDF generation & gap-free document numbering.
- **Week 18:** Backups, observability, and parity verification.
- **Week 19:** Gate 2 Pilot with live drafters.

---
*Signed off by Engineering & Legal Product Steering Committee.*

