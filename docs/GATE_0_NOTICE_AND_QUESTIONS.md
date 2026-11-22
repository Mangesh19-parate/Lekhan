# Gate 0 Client Kick-off: Data Security Notice & Decision Questionnaire

**Project:** Lekhan (Multilingual Property Legal Drafting Web App)  
**Recipient:** Partner / Managing Advocate & Office Administrator  
**Phase:** Phase 0 (Decisions & Technical Spike — Weeks 1–3)  
**Date:** Week 1 Kick-off  

---

## 1. Confidentiality & Data Security Notice

Before examining sample deeds or proceeding with technical implementation, this notice formally confirms the strict security and privacy standards governing all work:

1. **Isolation of Sample Archive**:
   * The archive of deed samples provided by your practice (`samples-private/`) is stored exclusively in a secure, encrypted local volume.
   * This directory is strictly isolated and excluded by automated repository filters (`.gitignore`). It will **never** be committed to version control, cloud repositories, or public networks.
2. **Synthetic Data in Code and Automated Tests**:
   * All development, automated CI pipelines, and golden tests use **100% synthetic (fictional) data**.
   * No real client names, Aadhaar numbers, PAN cards, phone numbers, or property boundaries will ever appear in test suites, application logs, or source code.
3. **No External Data Leakage**:
   * Offline developer tools (`corpus_tools`) process text locally to extract word frequency and template structures without exporting client details.
   * Upon completion of template extraction or upon your request, any raw unredacted sample copies will be securely deleted.
4. **Phase 0 Agreement & NDA**:
   * Mutual Non-Disclosure Agreement (NDA) and Phase 0 agreement must be countersigned prior to handing over original archives or proceeding past Gate 0.

---

## 2. Gate 0 Decision Questionnaire (Due by End of Week 2)

To ensure the technical spike (Week 3) produces templates matching your office workflow, please provide written decisions on the following questions:

### Question 1: Document Editing Font (Crucial Blocker)
* **Context:** 273 of the 310 analyzed `.docx` sample files use the legacy **Kruti Dev** font (non-Unicode), which prevents search, automated spell check, and digital portal integration. Lekhan natively generates modern **Unicode** (Noto Sans Devanagari / Mangal).
* **Decision Needed:**
  * [ ] **Option A (Recommended):** Typists/drafters will edit generated drafts in Microsoft Word using standard Unicode fonts. (Zero extra licensing, future-proof, registration-ready).
  * [ ] **Option B:** Office typists strictly insist on typing in Kruti Dev, requiring Lekhan to build a custom Unicode-to-Kruti export module. *(Note: This adds significant development overhead and requires licensing Kruti Dev).*

### Question 2: Legal Approver & Precedent Ownership (Blocker)
* **Context:** Software engineering cannot fabricate legal wording or statutory clauses.
* **Decision Needed:**
  * Who is the named advocate/lawyer who will dedicate 4–6 hours weekly to review template drafts and approve Marathi grammar combinations?
  * **Named Approver:** `________________________________________`
  * **Designation / Bar Reg:** `____________________________________`
  * Which specific sample files represent your firm's **gold-standard approved precedents** for the first set of deeds?

### Question 3: Confirmation of Wave 1 Document Priorities
* **Context:** Based on corpus frequency analysis, Wave 1 (Launch set) covers ~45% of practice volume across 10 templates.
* **Proposed Wave 1 Set:**
  1. *Marathi Plot Sale Deed (NIT / NMC Layout)* — **Priority 1 for Week 3 Spike**
  2. *Marathi Plot Agreement to Sell (Isar Pawti / Sathekhat)*
  3. *Marathi Flat / Apartment Sale Deed*
  4. *Marathi Commercial Shop Sale Deed*
  5. *Marathi Agricultural Land Sale Deed*
  6. *Marathi General Power of Attorney (GPA)*
  7. *English Flat Sale Deed*
  8. *English Flat Agreement to Sell*
  9. *English General Power of Attorney (GPA)*
  10. *Marathi Plot Agreement with Possession*
* **Decision Needed:** Does this list match your office's current monthly transaction volume? List any substitutions:
  * `_____________________________________________________________`

### Question 4: Registration Portal Data-Entry Workflow
* **Context:** Drafters currently retype parties and property details into the government registration portal. Lekhan can generate an assistive "portal data sheet" text block to eliminate double entry.
* **Decision Needed:**
  * What exact text format or field order does your operator use when entering transaction facts into the portal?

### Question 5: Hosting & Deployment Environment
* **Decision Needed:**
  * [ ] Local on-premises server / office mini-server (complete local data sovereignty).
  * [ ] Dedicated private cloud VM hosted in an Indian region (e.g. AWS Mumbai / GCP Delhi).

---

## 3. Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| Lead Developer | | | |
| Managing Advocate / Client | | | |

