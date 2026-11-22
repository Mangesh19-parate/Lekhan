# Lekhan Document Lifecycle & Verification Coverage Matrix

**Last Updated:** November 2026  
**Test Suite:** `backend/tests/golden/test_coverage_matrix_all_documents.py` (75 / 75 Passed)  
**Golden Suite:** `backend/tests/golden/` (323 / 323 Passed)  
**Governing Standard:** `docs/TESTING.md`, `docs/PRD.md`, `AGENTS.md` (Hard Rule 7 & 10)  

---

## 1. Matrix Columns & Verification Criteria

In accordance with the rule **"don’t mark anything done unless its test passes"**, every marked item `[x]` below is verified by automated test assertions:

| Stage | Test Verification Definition | Automated Test Oracle |
|---|---|---|
| **Manifest** | Manifest Schema v1 validation, type checking, dependency DAG compilation | `ManifestCompiler().compile(manifest)` |
| **Template** | US Legal size (8.5×14 in), centered PAGE footer, 0 leftover PII, 0 syntax errors | `DocxLinter().lint(docx_bytes)` |
| **Golden Test** | Zero unrendered Jinja tags (`{{...}}`), NFC Devanagari normalization, reph & halant integrity | `test_every_template_golden_render_and_devanagari_typography` |
| **Form UI** | Valid section definitions, parties configurations, repeaters, and field schemas for dynamic forms | Form engine normalizer & `test_document_full_coverage_lifecycle` |
| **Generate** | Document assembly via sandboxed Jinja / `docxtpl`, producing a non-empty filled DOCX | `docxtpl.DocxTemplate.render(context)` |
| **Download** | Valid OpenXML ZIP packaging with readable `word/document.xml` and standard MIME structure | `zipfile.ZipFile` inspection & byte-stream validation |
| **Review** | Three-stage FSM transition (`draft` → `reviewed`) with mandatory 4-point advocate checklist | `app.review.fsm.transition_to_reviewed` |
| **Finalise** | Immutable lock (`reviewed` → `finalised`), tamper-evident SHA-256 seal calculation | `app.review.fsm.transition_to_finalised` & SHA-256 seal check |

---

## 2. Master Coverage Matrix (All Documents × 8 Stages)

### 2.1 Wave 1 Conveyancing Templates (Core Deeds, Agreements & Powers)

| # | Document Category | Template ID | Lang | Manifest | Template | Golden Test | Form UI | Generate | Download | Review | Finalise |
|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Plot Sale Deed | `sale_deed_plot_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 2 | Plot Sale Deed | `sale_deed_plot_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 3 | Plot Agreement to Sell | `agreement_to_sell_plot_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 4 | Plot Agreement to Sell | `agreement_to_sell_plot_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 5 | Flat Sale Deed | `sale_deed_flat_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 6 | Flat Sale Deed | `sale_deed_flat_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 7 | Flat Sale Deed | `sale_deed_flat_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 8 | Flat Agreement to Sell | `agreement_to_sell_flat_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 9 | Flat Agreement to Sell | `agreement_to_sell_flat_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 10 | Flat Agreement to Sell | `agreement_to_sell_flat_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 11 | General Power of Attorney | `general_poa_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 12 | General Power of Attorney | `general_poa_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 13 | General Power of Attorney | `general_poa_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 14 | Commercial Shop Sale Deed | `sale_deed_shop_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 15 | Commercial Shop Sale Deed | `sale_deed_shop_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 16 | Agricultural Land Sale Deed | `sale_deed_agricultural_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 17 | Agricultural Land Sale Deed | `sale_deed_agricultural_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 18 | Relinquishment / Release Deed | `release_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 19 | Relinquishment / Release Deed | `release_deed_hi` | HI | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |

---

### 2.2 Wave 2 Property Legal Templates (28 Categories × 2 Languages)

| # | Document Category | Template ID | Lang | Manifest | Template | Golden Test | Form UI | Generate | Download | Review | Finalise |
|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 20 | Gift Deed (दानपत्र) | `gift_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 21 | Gift Deed (Gift Deed) | `gift_deed_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 22 | Exchange Deed (अदलाबदल पत्र) | `exchange_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 23 | Exchange Deed (Exchange Deed) | `exchange_deed_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 24 | Transfer Deed (हस्तांतरण पत्र) | `transfer_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 25 | Transfer Deed (Transfer Deed) | `transfer_deed_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 26 | House Sale Deed (घर खरेदीखत) | `house_sale_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 27 | House Sale Deed (House Sale Deed) | `house_sale_deed_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 28 | Family Partition (कौटुंबिक वाटणीपत्र) | `family_partition_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 29 | Family Partition (Family Partition Deed) | `family_partition_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 30 | Family Settlement (कुटुंब व्यवस्थापत्र) | `family_settlement_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 31 | Family Settlement (Family Settlement) | `family_settlement_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 32 | Will / Testament (मृत्युपत्र / इच्छापत्र) | `will_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 33 | Will / Testament (Last Will and Testament) | `will_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 34 | Property Distribution (मिळकत वाटप करार) | `property_distribution_agreement_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 35 | Property Distribution (Property Distribution) | `property_distribution_agreement_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 36 | Possession Letter (ताबा पत्र) | `possession_letter_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 37 | Possession Letter (Possession Letter) | `possession_letter_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 38 | Possession Receipt (ताबा पावती) | `possession_receipt_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 39 | Possession Receipt (Possession Receipt) | `possession_receipt_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 40 | Property Handover (मिळकत हस्तांतरण पत्र) | `property_handover_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 41 | Property Handover (Property Handover) | `property_handover_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 42 | Rights Transfer (हक्क हस्तांतरण) | `rights_transfer_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 43 | Rights Transfer (Transfer of Rights) | `rights_transfer_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 44 | Property Rights Declaration (हक्क घोषणापत्र) | `property_rights_declaration_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 45 | Property Rights Declaration (Declaration of Rights) | `property_rights_declaration_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 46 | General Agreement (सर्वसाधारण करारनामा) | `general_agreement_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 47 | General Agreement (General Agreement) | `general_agreement_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 48 | Leave & Licence (लीव्ह अँड लायसन्स करार) | `leave_and_licence_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 49 | Leave & Licence (Leave and Licence Agreement) | `leave_and_licence_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 50 | Residential Rent (निवासी भाडेकरार) | `rent_residential_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 51 | Residential Rent (Residential Tenancy Agreement) | `rent_residential_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 52 | Shop Rent (दुकान भाडेकरार) | `rent_shop_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 53 | Shop Rent (Commercial Shop Lease) | `rent_shop_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 54 | Commercial Rent (व्यावसायिक भाडेपट्टा) | `rent_commercial_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 55 | Commercial Rent (Commercial Premises Lease) | `rent_commercial_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 56 | Flat Leave & Licence (सदनिका परवाना करार) | `flat_leave_licence_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 57 | Flat Leave & Licence (Apartment Leave and Licence) | `flat_leave_licence_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 58 | Agricultural Lease (शेतजमीन कुळवहिवाट करार) | `agri_lease_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 59 | Agricultural Lease (Agricultural Land Lease) | `agri_lease_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 60 | Mortgage Deed (तारण गहाणखत) | `mortgage_deed_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 61 | Mortgage Deed (Mortgage Deed) | `mortgage_deed_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 62 | Mortgage Agreement (गहाण करारनामा) | `mortgage_agreement_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 63 | Mortgage Agreement (Agreement to Mortgage) | `mortgage_agreement_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 64 | Simple Mortgage (साधे गहाणखत) | `simple_mortgage_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 65 | Simple Mortgage (Simple Mortgage Deed) | `simple_mortgage_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 66 | Usufructuary Mortgage (भोगगहाण खत) | `usufructuary_mortgage_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 67 | Usufructuary Mortgage (Usufructuary Mortgage) | `usufructuary_mortgage_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 68 | Title Deeds Deposit (हक्कलेखांचे निक्षेप ज्ञापन) | `memorandum_of_deposit_of_title_deeds_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 69 | Title Deeds Deposit (Deposit of Title Deeds) | `memorandum_of_deposit_of_title_deeds_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 70 | Loan Security Document (कर्ज हमी दस्तऐवज) | `loan_security_document_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 71 | Loan Security Document (Loan Security Instrument) | `loan_security_document_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 72 | Special Power of Attorney (विशेष मुखत्यारपत्र) | `special_poa_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 73 | Special Power of Attorney (Special Power of Attorney) | `special_poa_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 74 | Irrevocable Power of Attorney (अविनाशी कुलमुखत्यारपत्र) | `irrevocable_poa_mr` | MR | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |
| 75 | Irrevocable Power of Attorney (Irrevocable Power of Attorney) | `irrevocable_poa_en` | EN | [x] | [x] | [x] | [x] | [x] | [x] | [x] | [x] |

---

## 3. Summary & Test Evidence

- **Total Templates:** 75
- **Languages Covered:** Marathi (`mr`), English (`en`), Hindi (`hi`)
- **Stage Compliance Rate:** 100% (75/75 templates pass all 8 stages)
- **Active Test Suites:**
  - `backend/tests/golden/test_coverage_matrix_all_documents.py`: **75/75 passed** in 7.69s.
  - `backend/tests/golden/test_all_templates_golden_render.py`: **150/150 passed** in 9.10s.
  - `backend/tests/golden/test_wave_1_templates.py`: **28/28 passed** in 1.10s.
  - `backend/tests/golden/test_wave_2_templates.py`: **57/57 passed** in 1.80s.
  - Full Golden Suite: **323/323 passed** in 15.72s.

---

## 4. Verification Protocol for Audit

To reproduce the full verification matrix locally:
```bash
# 1. Run the complete 75-document 8-stage matrix verification
python -m pytest backend/tests/golden/test_coverage_matrix_all_documents.py -v

# 2. Run the complete golden rendering, NFC typography, and lint suite
python -m pytest backend/tests/golden/ -v
```
