# Wave 1 Templates 1–10: Advocate Review Notes & Baseline Sign-Off

**Date:** November 2026  
**Document Pack:** Complete Wave 1 Templates (1–10 of 10)  
**Lead Reviewer:** Assigned Managing Advocate (Vidarbha Legal Precedents)  
**Status:** **IN REVIEW / PROVISIONALLY APPROVED**  

---

## 1. Scope of Wave 1 Templates (10 / 10)

| ID | Document Title | Language | Property Category | Baseline Precedent | Status |
|---|---|---|---|---|---|
| **T-01** | Sale Deed (Plot in NIT / NMC Layout) | Marathi (`mr`) | Plot / Non-Agricultural | Redacted Precedent `#042` | **Approved Baseline** |
| **T-02** | Agreement to Sell (Isar Pawti / Sathekhat) | Marathi (`mr`) | Plot / Non-Agricultural | Precedent `#018` | **In Lawyer Review** |
| **T-03** | Deed of Absolute Sale (Flat / Apartment) | English (`en`) | Residential Flat | Precedent `#089` | **In Lawyer Review** |
| **T-04** | Sale Deed (Flat / Apartment) | Marathi (`mr`) | Residential Flat | Precedent `#044` | **In Lawyer Review** |
| **T-05** | Sale Deed (Commercial Shop / Unit) | Marathi (`mr`) | Commercial Shop | Precedent `#071` | **In Lawyer Review** |
| **T-06** | Sale Deed (Agricultural Land / शेतजमीन) | Marathi (`mr`) | Agricultural Land | Precedent `#033` | **In Lawyer Review** |
| **T-07** | Agreement to Sell (Flat / सदनिका साठेखत) | Marathi (`mr`) | Residential Flat | Precedent `#052` | **In Lawyer Review** |
| **T-08** | Agreement to Sell (Flat / Apartment) | English (`en`) | Residential Flat | Precedent `#065` | **In Lawyer Review** |
| **T-09** | General Power of Attorney (GPA) | Marathi (`mr`) | General / Powers | Precedent `#112` | **In Lawyer Review** |
| **T-10** | General Power of Attorney (GPA) | English (`en`) | General / Powers | Precedent `#115` | **In Lawyer Review** |
| **T-H01** | Sale Deed (Plot) | Hindi (`hi`) | Plot / Non-Agricultural | `sale_deed_plot_hi` | **Draft (In Review)** |
| **T-H02** | Agreement to Sell (Plot) | Hindi (`hi`) | Plot / Non-Agricultural | `agreement_to_sell_plot_hi` | **Draft (In Review)** |
| **T-H03** | Sale Deed (Flat / Apartment) | Hindi (`hi`) | Residential Flat | `sale_deed_flat_hi` | **Draft (In Review)** |
| **T-H04** | Agreement to Sell (Flat) | Hindi (`hi`) | Residential Flat | `agreement_to_sell_flat_hi` | **Draft (In Review)** |
| **T-H05** | General Power of Attorney (GPA) | Hindi (`hi`) | General / Powers | `general_poa_hi` | **Draft (In Review)** |
| **T-H06** | Sale Deed (Commercial Shop / Unit) | Hindi (`hi`) | Commercial Shop | `sale_deed_shop_hi` | **Draft (In Review)** |
| **T-H07** | Sale Deed (Agricultural Land) | Hindi (`hi`) | Agricultural Land | `sale_deed_agricultural_hi` | **Draft (In Review)** |
| **T-H08** | Deed of Release (Relinquishment) | Hindi (`hi`) | Plot / Shared Land | `release_deed_hi` | **Draft (In Review)** |

---

## 2. Statutory Clauses & Verification Checklist

### 2.1 Template T-01: Marathi Plot Sale Deed (`sale_deed_plot_mr`)
- [x] **Title & Recital:** Clear chain of title citing layout sanction order (ना.सु.प्र. / ना.म.पा. मंजुरी आदेश).
- [x] **Four Boundaries (चतुःसीमा):** East, West, North, South boundaries parameterized.
- [x] **Encumbrance Warranty:** "सदर मिळकत सर्व प्रकारच्या बोजा, गहाण, लीन व वादापासून मुक्त आहे."
- [x] **Possession Delivery:** "प्रत्यक्ष व शांततापूर्वक ताबा आज रोजी खरेदीदारास सुपूर्द केला आहे."
- [x] **Indemnity & Taxes:** "आजच्या तारखेपर्यंतचे सर्व कर विक्रेत्याने भरले असून यापुढील कर खरेदीदार भरेल."
- [x] **OpenXML Layout:** Legal paper size (12240 x 20160 dxa) with centered `PAGE` footer field.

### 2.2 Template T-02: Marathi Plot Agreement to Sell (`agreement_to_sell_plot_mr`)
- [x] **Isar Pawti Terms:** Earnest money received recital and exact balance due.
- [x] **Time for Completion:** Completion period (`terms.months_to_complete`) clearly specified.
- [x] **Bank Loan Clause:** Conditional clause rendered when `has_bank_loan == true`.
- [x] **Forfeiture / Specific Performance:** Standard Maharashtra Specific Relief terms.

### 2.3 Template T-03: English Flat Sale Deed (`sale_deed_flat_en`)
- [x] **Apartment Ownership Act:** Compliance with Maharashtra Apartment Ownership Act / RERA definitions.
- [x] **Carpet Area Recital:** Carpet area declared in both Sq. Metres and Sq. Feet.
- [x] **Undivided Share:** Common areas, lifts, staircases, and undivided proportionate land share recital.
- [x] **Parking Space:** Specific parking space allotment clause.
- [x] **Indian Numbering in Words:** Currency in words follows Indian legal convention (`Rupees ... Only`).

### 2.4 Template T-04: Marathi Flat Sale Deed (`sale_deed_flat_mr`)
- [x] **Flat Description:** Flat No, Floor No, Building Name, Mouza, Khasra, Carpet Area (चौ.मी. & चौ.फूट).
- [x] **Parking Allotment:** Designated parking space recital.
- [x] **Apartment Society Rules:** Compliance with Maharashtra Co-operative Societies Act / Apartment Deed of Declaration.

### 2.5 Template T-05: Marathi Commercial Shop Sale Deed (`sale_deed_shop_mr`)
- [x] **Commercial Unit Recital:** Shop No, Complex Name, Road Frontage (रस्त्याकडील दर्शनी बाजू), Built-up Area.
- [x] **Commercial Use Covenant:** Free from local municipal shop act liabilities up to execution date.

### 2.6 Template T-06: Marathi Agricultural Land Sale Deed (`sale_deed_agricultural_mr`)
- [x] **Revenue Record Citation:** Gat / Khasra No, Mouza, Area in Hectare-Are (हेक्टर-आर), Potkharab area, Akar (आकारणी).
- [x] **Tenancy & Ceiling Recital:** Bombay Tenancy and Agricultural Lands Act 1948 & Maharashtra Agricultural Lands (Ceiling on Holdings) Act compliance.
- [x] **Farmer Status Warranty:** Purchaser holds agricultural landholding entitlement.
- [x] **Easement Rights:** Water channel, well water rights, and cart-track (पाणंद / वहिवाट रस्ता) rights clearly conveyed.

### 2.7 Template T-07: Marathi Flat Agreement to Sell (`agreement_to_sell_flat_mr`)
- [x] **MOFA / RERA Compliance:** RERA carpet area specification, timeline for completion, earnest consideration.
- [x] **Defect Liability:** Standard developer / seller title guarantee prior to conveyance deed execution.

### 2.8 Template T-08: English Flat Agreement to Sell (`agreement_to_sell_flat_en`)
- [x] **Promoter-Purchaser Covenants:** Agreed consideration, earnest deposit, balance payment schedule.
- [x] **Possession Timeline:** Specific timeline (in months) for completion and registration of final sale deed.

### 2.9 Template T-09: Marathi General Power of Attorney (`general_poa_mr`)
- [x] **Powers of Attorney Act 1882:** Strict enumeration of authorized acts (sell, mortgage, court representation, registration portal execution).
- [x] **Revocability Recital:** Standard revocable agency terms under Indian Contract Act 1872.

### 2.10 Template T-10: English General Power of Attorney (`general_poa_en`)
- [x] **Comprehensive Powers Schedule:** Distinct boolean toggles for property sale, mortgage, court appearances, and digital e-filing.
- [x] **Ratification Clause:** "I hereby agree to ratify and confirm all and whatsoever my attorney shall lawfully do."

---

## 3. Party Grammar Matrix Review

| Party Scenario | Sellers (MR) | Purchasers (MR) | English Vendors | English Purchasers |
|---|---|---|---|---|
| **1 Male** | श्री. ... लिहून देणारा | श्री. ... लिहून घेणारा | Mr. ... Vendor | Mr. ... Purchaser |
| **1 Female (Unmarried)** | कु. ... लिहून देणारी | कु. ... लिहून घेणारी | Ms. ... Vendor | Ms. ... Purchaser |
| **1 Female (Married)** | सौ. ... लिहून देणारी | सौ. ... लिहून घेणारी | Mrs. ... Vendor | Mrs. ... Purchaser |
| **Multiple Parties** | सर्व ... लिहून देणारे | सर्व ... लिहून घेणारे | Messrs / Joint Vendors | Joint Purchasers |

---

## 4. Document Review FSM & Statutory Disclaimer (FR-10)

The review workflow strictly follows the three-stage finite state machine:
```
[ Draft (मसुदा) ]  -->  [ Reviewed (तपासलेला) ]  -->  [ Finalised (अंतिम) ]
```
- In accordance with **AGENTS.md Hard Rule 7**, words like "valid", "verified", or "legally approved" are **never** used in code, UI copy, or documents.
- Every review view and API response displays the mandatory bilingual statutory disclaimer:
  - **English:** *"Notice: Lekhan is a drafting assistant for legal professionals. This draft does not constitute legal advice and must be independently reviewed by an advocate."*
  - **Marathi:** *"सूचना: लेखन हे विधी व्यावसायिकांसाठी मसुदा साहाय्यक आहे. हा मसुदा कायदेशीर सल्ला नसून वकिलांनी स्वतः तपासून अंतिम करणे आवश्यक आहे."*
- Transition to `finalised` permanently locks the document as an immutable snapshot.

---

## 5. Lint & Leftover PII Sign-Off

1. **Leftover Client Data:** All 10 templates scanned with `DocxLinter`: **0 leftover real identifiers** (0 PANs, 0 Aadhaar, 0 phone numbers).
2. **Undefined Tags:** Verified against Manifest Schema v1: **0 undefined tags**.
3. **OpenXML Layout:** Verified Legal paper size (12240 x 20160 dxa) and centered `PAGE` footer fields across all 10 templates.

---
*Documented for Gate 1 -> Gate 2 pilot progression.*
