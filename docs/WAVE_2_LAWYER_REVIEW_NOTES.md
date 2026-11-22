# Wave 2 Templates: Advocate Review Notes & Drafting Registry

**Date:** November 2026  
**Document Pack:** Complete Wave 2 Templates (28 Document Types / 56 Templates: MR & EN)  
**Lead Reviewer:** Assigned Managing Advocate (Vidarbha Legal Precedents)  
**Status:** **DRAFT (मसुदा) — PENDING ADVOCATE REVIEW** (Marked Draft until formal advocate sign-off)

---

## 1. Scope of Wave 2 Templates (28 Categories / 56 Templates)

All templates are generated via `corpus_tools` with run-aware Unicode conversion, strict PII redaction (AGENTS.md Hard Rule 1), OpenXML US Legal layout (12240 x 20160 dxa), centered PAGE/NUMPAGES footer, and Clause Library integration (`backend/app/templates/clauses.py`).

| # | Document Category | Marathi ID (`mr`) | English ID (`en`) | Precedent Source Folder | Reused Clause(s) | Review Status |
|---|---|---|---|---|---|---|
| 1 | **Gift Deed** (दानपत्र) | `gift_deed_mr` | `gift_deed_en` | `VISHAL DOCUMENTS/GIFT DEED` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 2 | **Exchange Deed** (अदलाबदल पत्र) | `exchange_deed_mr` | `exchange_deed_en` | `VISHAL DOCUMENTS/AAPSI VATNIPATRA` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 3 | **Transfer Deed** (हस्तांतरण पत्र) | `transfer_deed_mr` | `transfer_deed_en` | `VISHAL DOCUMENTS/HAKKASOD LEKH` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 4 | **House Sale Deed** (घर / इमारत खरेदीखत) | `house_sale_deed_mr` | `house_sale_deed_en` | `VISHAL DOCUMENTS/SALE DEED MARATHI` / `SALE DEED ENGLISH` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 5 | **Family Partition** (कौटुंबिक वाटणीपत्र) | `family_partition_mr` | `family_partition_en` | `VISHAL DOCUMENTS/AAPSI VATNIPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 6 | **Family Settlement** (कौटुंबिक समजोता पत्र) | `family_settlement_mr` | `family_settlement_en` | `VISHAL DOCUMENTS/SETTLEMENT DEED` / `SAMJHOTA PATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 7 | **Will** (मृत्युपत्र / इच्छापत्र) | `will_mr` | `will_en` | `VISHAL DOCUMENTS/MRUTUPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 8 | **Property Distribution Agreement** (मिळकत वाटप करार) | `property_distribution_agreement_mr` | `property_distribution_agreement_en` | `VISHAL DOCUMENTS/AAPSI VATNIPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 9 | **Possession Letter** (ताबा पत्र) | `possession_letter_mr` | `possession_letter_en` | `VISHAL DOCUMENTS/KABJAPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 10 | **Possession Receipt** (ताबा पावती) | `possession_receipt_mr` | `possession_receipt_en` | `VISHAL DOCUMENTS/KABJAPATRA` / `KAPJA PATRA RADHA LEKH` | `witness_attestation` | **Draft (मसुदा)** |
| 11 | **Property Handover** (मिळकत सुपूर्द पत्र) | `property_handover_mr` | `property_handover_en` | `VISHAL DOCUMENTS/KABJAPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 12 | **Rights Transfer** (हक्क हस्तांतरण पत्र) | `rights_transfer_mr` | `rights_transfer_en` | `VISHAL DOCUMENTS/HAKKASOD LEKH` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 13 | **Property Rights Declaration** (हक्क घोषणापत्र) | `property_rights_declaration_mr` | `property_rights_declaration_en` | `VISHAL DOCUMENTS/GHOSHNAPATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 14 | **General Agreement** (सर्वसाधारण करारनामा) | `general_agreement_mr` | `general_agreement_en` | `VISHAL DOCUMENTS/AGREEMENT MARATHI` / `AGREEMENT ENGLISH` | `witness_attestation` | **Draft (मसुदा)** |
| 15 | **Leave and Licence** (भाडेतत्वावर वापर करार) | `leave_and_licence_mr` | `leave_and_licence_en` | `VISHAL DOCUMENTS/LEAVE AND LICENCE AGREEMENT` | `witness_attestation` | **Draft (मसुदा)** |
| 16 | **Rent Residential** (निवासी भाडेकरार) | `rent_residential_mr` | `rent_residential_en` | `VISHAL DOCUMENTS/RENT AGREEMENT` / `KIRAYA PATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 17 | **Rent Shop** (दुकान भाडेकरार) | `rent_shop_mr` | `rent_shop_en` | `VISHAL DOCUMENTS/RENT AGREEMENT` / `KIRAYA PATRA` | `witness_attestation` | **Draft (मसुदा)** |
| 18 | **Rent Commercial** (व्यावसायिक जागा भाडेकरार) | `rent_commercial_mr` | `rent_commercial_en` | `VISHAL DOCUMENTS/RENT AGREEMENT` | `witness_attestation` | **Draft (मसुदा)** |
| 19 | **Flat Leave and Licence** (सदनिका लिव्ह अँड लायसन्स) | `flat_leave_licence_mr` | `flat_leave_licence_en` | `VISHAL DOCUMENTS/LEAVE AND LICENCE AGREEMENT` | `witness_attestation` | **Draft (मसुदा)** |
| 20 | **Agricultural Lease** (शेतजमीन खंडपत्र) | `agri_lease_mr` | `agri_lease_en` | `VISHAL DOCUMENTS/SALE DEED KHETI` / `AGREEMENT MARATHI` | `witness_attestation` | **Draft (मसुदा)** |
| 21 | **Mortgage Deed** (गहाणखत) | `mortgage_deed_mr` | `mortgage_deed_en` | `VISHAL DOCUMENTS/MORTAGE DEED` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 22 | **Mortgage Agreement** (गहाण करारनामा) | `mortgage_agreement_mr` | `mortgage_agreement_en` | `VISHAL DOCUMENTS/MORTAGE DEED` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 23 | **Simple Mortgage** (साधे गहाणखत) | `simple_mortgage_mr` | `simple_mortgage_en` | `VISHAL DOCUMENTS/MORTAGE DEED` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 24 | **Usufructuary Mortgage** (भोगगहाणखत) | `usufructuary_mortgage_mr` | `usufructuary_mortgage_en` | `VISHAL DOCUMENTS/MORTAGE DEED` | `witness_attestation` | **Draft (मसुदा)** |
| 25 | **MODTD** (दस्तऐवज ठेव स्मरणपत्र) | `memorandum_of_deposit_of_title_deeds_mr` | `memorandum_of_deposit_of_title_deeds_en` | `VISHAL DOCUMENTS/MORTAGE DEED` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |
| 26 | **Loan Security Document** (कर्ज सुरक्षा दस्त) | `loan_security_document_mr` | `loan_security_document_en` | `VISHAL DOCUMENTS/DEED OF GUARANTEE` / `loan kararnama` | `witness_attestation` | **Draft (मसुदा)** |
| 27 | **Special POA** (विशेष मुखत्यारपत्र) | `special_poa_mr` | `special_poa_en` | `VISHAL DOCUMENTS/SPECIAL POWER` | `witness_attestation` | **Draft (मसुदा)** |
| 28 | **Irrevocable POA** (अपरिवर्तनीय कुलमुखत्यारपत्र) | `irrevocable_poa_mr` | `irrevocable_poa_en` | `VISHAL DOCUMENTS/AAMUKHTYARNAAMA` / `MUKHTYARNAMA` | `title_warranty`, `witness_attestation` | **Draft (मसुदा)** |

---

## 2. Statutory Covenants & Advocate Verification Checklist

### 2.1 Gifts and Conveyance (Categories 1–4)
- [x] **Transfer of Property Act 1882 (Sec 122 & 123 - Gift Deed):**
  - Express recital of gift made voluntarily and out of natural love and affection without monetary consideration.
  - Acceptance by Donee during the lifetime of the Donor explicitly recited.
  - Attestation by two independent witnesses mandated.
- [x] **Sec 118 (Exchange Deed):**
  - Mutual conveyance of properties (Schedule 'A' for Schedule 'B') without monetary imbalance.
  - Mutual warranty of clear, marketable title and peaceful possession.
- [x] **Sec 54 (Sale / Transfer Deed):**
  - Transfer of absolute ownership, delivery of physical possession, and clear discharge of municipal dues up to execution date.

### 2.2 Family Arrangements, Partitions & Wills (Categories 5–8)
- [x] **Hindu Succession Act 1956 & Coparcenary Partition:**
  - Recognition of ancestral title and pre-existing rights.
  - Mutual release of rights in allotted shares of other coparceners.
  - Equal division without future claims or family disputes.
- [x] **Family Settlement Agreement (Kale v. Director of Consolidation):**
  - Recital of existing or bona fide disputes.
  - Compromise arrived at with advice of family elders to maintain amity and peace.
- [x] **Indian Succession Act 1925 (Sec 59 & 63 - Last Will and Testament):**
  - Express statement of sound mind, memory, and understanding (शुद्धीत व उत्तम स्वास्थ्यात).
  - Explicit revocation of all previous wills and testamentary instruments.
  - Attestation by minimum two witnesses who witnessed testator's execution.

### 2.3 Possession Documents (Categories 9–11)
- [x] **Specific Relief Act 1963 (Sec 5 & 6):**
  - Concrete identification of delivered premises.
  - Acknowledgement of receiving physical, vacant, and peaceful possession without reservation.
  - Apportionment of property taxes and utility liabilities from the date of physical delivery.

### 2.4 Declarations and General Agreements (Categories 12–14)
- [x] **Indian Contract Act 1872 (Sec 10 - Valid Contracts):**
  - Free consent, lawful consideration, competent parties.
  - Severability and specific performance remedies.
- [x] **Solemn Declarations:**
  - Solemn affirmation of clear and unencumbered title on affidavit for mutation before municipal/revenue records.

### 2.5 Tenancy, Leases & Licences (Categories 15–20)
- [x] **Maharashtra Rent Control Act 1999 (Sec 24 - Leave & Licence):**
  - Explicit declaration of temporary permissive licence (परवाना) for defined term (11 months standard).
  - Explicit negative covenant: No tenancy or sub-tenancy rights created.
  - Refundable interest-free security deposit return covenant.
- [x] **Commercial Tenancy & Shop Act:**
  - Strict compliance with municipal business regulations and trade licences.
- [x] **Agricultural Lease (खंडपत्र):**
  - Maharashtra Agricultural Lands (Ceiling on Holdings) Act and Tenancy law compliance.
  - Water rights, well easement, and cart-track (वहिवाट रस्ता) access protection.

### 2.6 Mortgages & Collateral Instruments (Categories 21–26)
- [x] **Transfer of Property Act 1882 (Sec 58):**
  - **Simple Mortgage (Sec 58b):** Personal covenant to pay; right to cause property to be sold on default without physical delivery of possession.
  - **Usufructuary Mortgage (Sec 58d):** Delivery of possession to Mortgagee; right to appropriate rents and profits towards interest and principal.
  - **Equitable Mortgage / MODTD (Sec 58f):** Formal memorandum recording deposit of title deeds with intent to create security in favor of lender.
- [x] **Personal Guarantee & Loan Security:**
  - Joint and several liability of Principal Borrower and Personal Guarantor.

### 2.7 Powers of Attorney (Categories 27–28)
- [x] **Powers of Attorney Act 1882 & Indian Contract Act 1872 (Sec 202):**
  - **Special POA:** Restricted to specific ministerial acts before Sub-Registrar / municipal authorities; no right to alienate or mortgage.
  - **Irrevocable POA:** Agency coupled with valuable interest/consideration under Sec 202; expressly irrevocable by Principal or heirs.

---

## 3. Party Grammar Matrix Verification

All generated templates strictly follow the Marathi and English gender/number matrix:

| Scenario | Marathi Singular Male | Marathi Singular Female | Marathi Plural / Joint | English Individual | English Joint |
|---|---|---|---|---|---|
| **Donor / Releasor** | श्री. ... लिहून देणारे / दाता | सौ. / कु. ... लिहून देणाऱ्या / दाती | सर्व संयुक्त लिहून देणारे | Donor | Joint Donors |
| **Donee / Releasee** | श्री. ... लिहून घेणारे / ग्रहिता | सौ. / कु. ... लिहून घेणाऱ्या / ग्रहिता | सर्व संयुक्त लिहून घेणारे | Donee | Joint Donees |
| **Landlord / Licensor** | श्री. ... परवाना देणारे | सौ. / कु. ... परवाना देणाऱ्या | सर्व संयुक्त परवाना देणारे | Licensor / Landlord | Joint Licensors |
| **Tenant / Licensee** | श्री. ... परवाना घेणारे | सौ. / कु. ... परवाना घेणाऱ्या | सर्व संयुक्त परवाना घेणारे | Licensee / Tenant | Joint Licensees |
| **Mortgagor** | श्री. ... गहाण देणारे | सौ. / कु. ... गहाण देणाऱ्या | सर्व संयुक्त गहाण देणारे | Mortgagor | Joint Mortgagors |
| **Mortgagee** | श्री. ... गहाण घेणारे / बँक | बँक / वित्तीय संस्था | सर्व संयुक्त गहाण घेणारे | Mortgagee / Bank | Co-Mortgagees |
| **Principal** | श्री. ... अधिकार देणारे | सौ. / कु. ... अधिकार देणाऱ्या | सर्व संयुक्त अधिकार देणारे | Principal | Joint Principals |
| **Attorney** | श्री. ... कुलमुखत्यार | सौ. / कु. ... कुलमुखत्यार | सर्व संयुक्त कुलमुखत्यार | Attorney | Joint Attorneys |

---

## 4. Finite State Machine & Statutory Disclaimer (FR-10 / Hard Rule 7)

In strict accordance with **AGENTS.md Hard Rule 7** and **docs/PRD.md FR-10**:
1. All 56 templates are flagged with `"status": "draft"` in their manifests.
2. Words like "valid", "verified", or "legally approved" are **strictly prohibited** in templates, code, and comments.
3. Every template embeds the mandatory computer-generated draft advisory:
   - **Marathi (`mr`):** `[सूचना: हा संगणक-व्युत्पन्न मसुदा असून केवळ सुलभ संपादन व संदर्भासाठी आहे. अंतिम नोंदणीपूर्वी संबंधित वकिलांकडून तपासणी आवश्यक आहे.]`
   - **English (`en`):** `[NOTICE: This is a computer-generated draft provided solely for reference and editing. Verification by an advocate is required prior to final registration.]`
4. Advocate sign-off workflow follows:
   ```
   [ Draft (मसुदा) ]  -->  [ In Review (तपासणीत) ]  -->  [ Approved (मंजूर) ]
   ```
   All 56 templates remain in `Draft (मसुदा)` until the assigned managing advocate conducts individual verification in Microsoft Word and signs off.
