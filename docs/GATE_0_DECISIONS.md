# Gate 0 Decisions Record (Architecture Decision Record)

**Status:** APPROVED  
**Date:** Week 2 Exit Check  
**Participants:** Lead Developer, Managing Advocate / Client, Office Administrator  
**Governing Documents:** [docs/PRD.md](file:///c:/Software%20for%20Drafting/docs/PRD.md), [docs/PLAN.md](file:///c:/Software%20for%20Drafting/docs/PLAN.md), [AGENTS.md](file:///c:/Software%20for%20Drafting/AGENTS.md)  

---

## 1. Decision 1: Document Encoding and Editing Font (Blocker Resolved)
* **Question:** Do typists need to edit generated files in Kruti Dev font, or will they edit in Unicode?
* **Decision:** **Unicode is canonical across all layers.**
  * All generated `.docx` output files will be modern UTF-8 Unicode.
  * Drafters and typists will edit documents in Microsoft Word 2016+ using standard Devanagari input (InScript or Google Input Tools) with Unicode fonts.
  * Kruti Dev export is explicitly **deferred** (marked Won't in 6-month release, PRD Section 4).
  * **Rationale:** Unicode allows full-text search, leftover PII detection, automatic spell-checking, and zero-loss copying into government registration portals.

## 2. Decision 2: Typography & Font Pairing
* **Decision:**
  * **UI & Web Preview:** Inter (Latin) + Noto Sans Devanagari (Marathi/Hindi).
  * **Document Master (DOCX):** Noto Serif Devanagari / Mangal for printed legal output.
  * **License:** Noto fonts are open-source (SIL Open Font License) and installed on the local server and dev machines. No proprietary or unlicensed font files will be bundled or committed.

## 3. Decision 3: Wave 1 Document Scope Locked
* **Decision:** The launch set covers the 10 highest-frequency precedents identified in corpus analysis:
  1. *Marathi Plot Sale Deed (NIT / NMC Layout)* — **Target for Week 3 Spike**
  2. *Marathi Plot Agreement to Sell (Isar Pawti / Sathekhat)*
  3. *Marathi Flat / Apartment Sale Deed*
  4. *Marathi Commercial Shop Sale Deed*
  5. *Marathi Agricultural Land Sale Deed*
  6. *Marathi General Power of Attorney (GPA)*
  7. *English Flat Sale Deed*
  8. *English Flat Agreement to Sell*
  9. *English General Power of Attorney (GPA)*
  10. *Marathi Plot Agreement to Sell with Possession*

## 4. Decision 4: Legal Reviewer & Precedent Ownership
* **Decision:**
  * The managing advocate has assigned a dedicated legal reviewer available for 4–6 hours weekly.
  * Redacted sample deed `#042` (Plot Sale Deed, NMC Layout) is confirmed as the official legal baseline for the Week 3 technical spike.
  * All grammar agreement tables (e.g., 1M, 1F, mixed parties) must be signed off by the lawyer before marking templates as `Approved`.

## 5. Decision 5: Hosting & Deployment Model
* **Decision:** **On-Premises Dedicated Server.**
  * Deployment target is an Ubuntu LTS dedicated workstation in the firm's Nagpur office running Docker Compose + Caddy.
  * Backups: Nightly encrypted automated dumps transferred to secure off-site storage.

---

## Sign-off Summary

| Role | Status | Date |
|---|---|---|
| Managing Advocate | Signed & Approved | Week 2 |
| Lead Developer | Implemented in Architecture | Week 2 |

