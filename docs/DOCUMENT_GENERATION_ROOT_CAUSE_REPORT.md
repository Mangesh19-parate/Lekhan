# Document Generation Root Cause Analysis Report

**Project:** Lekhan (Multilingual Property Legal Drafting Platform)  
**Author:** Principal Backend Engineer & Software Architect  
**Date:** November 25, 2026  
**Status:** Remediated & Verified  

---

## 1. Executive Summary

A critical defect was identified in Lekhan where users could enter property drafting information through the frontend form, submit the form, but the document generation pipeline failed to reliably generate and deliver a downloadable, correctly populated DOCX document.

A comprehensive audit of the entire execution chain revealed that the failure was not a cosmetic UI issue, but a combination of architectural bypasses, client-server contract mismatches, misleading template approval statuses, and absent pre-enqueue validation.

---

## 2. End-to-End Generation Flow Breakdown & Root Causes

```
User Input (Form)
      │
      ▼
Frontend Validation ─── [Bug 1: Misleading Fallback & Approved Badges]
      │
      ▼
Backend Pre-Enqueue ─── [Bug 2: Unvalidated Enqueue into Queue]
      │
      ▼
Job Queue (Postgres)
      │
      ▼
Background Worker ──── [Bug 3: SpikeGenerationError Treated as Transient]
      │
      ▼
Template Resolution ─── [Bug 4: DB Version Byte Bypassed Specialized Renderer]
      │
      ▼
Docx Engine ─────────── [Bug 5: Missing Sellers/Purchasers Derived Blocks]
      │
      ▼
Verification Gate ───── [Bug 6: StrictUndefined or Leftover {{ }} Exception]
      │
      ▼
Storage & DB Record ─── [Failure: Document Record Never Created]
      │
      ▼
Job Polling / Download ─ [Failure: Job Marked Failed or Stalled]
```

### Root Cause 1: Misleading Template Badges & Fallback Status (Frontend)
- **File:** `frontend/src/features/form_engine/TemplateSelectorModal.tsx`
- **Defect:** 
  1. Line 211 hardcoded `<Badge variant="approved" size="sm" label="Approved" />` for every template in the list, regardless of the template's actual lifecycle status.
  2. `FALLBACK_TEMPLATES` in `TemplateSelectorModal.tsx` and `DEFAULT_WAVE1_TEMPLATES` in `TemplateLibraryView.tsx` marked 5 draft templates (`agreement_to_sell_plot_mr`, `sale_deed_flat_mr`, `sale_deed_flat_en`, `general_poa_mr`, `general_poa_en`) as `"approved"`.
  3. In reality, the legal catalog contained 75 templates, where **only 1 (`sale_deed_plot_mr`) was approved**, and 74 were drafts.
- **Impact:** Users could select unapproved draft templates under the false impression that they were approved, submit them, and receive downstream generation failures.

### Root Cause 2: Specialized Marathi Renderer Bypass (Backend Generation Pipeline)
- **File:** `backend/app/generation/pipeline.py`
- **Defect:**
  In `GenerationPipelineFSM.process_job`:
  ```python
  # Former implementation:
  if template_id == "sale_deed_plot_mr" and template_bytes is None:
      normalized_payload = _normalize_payload(job.payload)
      input_data = PlotSaleDeedInput.model_validate(normalized_payload)
      docx_bytes = generate_plot_sale_deed_docx(input_data)
  else:
      docx_bytes = _render_template_docx(
          template_id, job.payload, docx_bytes_input=template_bytes
      )
  ```
  Whenever a template was pinned or loaded from a database `TemplateVersion` (`template_bytes is not None`), the specialized Marathi generator was **completely bypassed**.
- **Impact:** The generic `_render_template_docx` function received raw job payloads. The `sale_deed_plot_mr/template.docx` requires computed context fields (`{{ sellers_block }}`, `{{ purchasers_block }}`, `{{ total_consideration_words }}`, `{{ balance_amount_words }}`, `{{ payment_details_clause }}`), none of which exist in raw form payloads. Jinja2 under `StrictUndefined` raised exceptions or failed the leftover tag verification gate, causing jobs to fail.

### Root Cause 3: Function Signature Incompatibility in `spike_engine.py`
- **File:** `backend/app/generation/spike_engine.py`
- **Defect:** `generate_plot_sale_deed_docx(data, template_path=None)` only accepted a filesystem `Path`. It had no parameter to accept in-memory `template_bytes`.
- **Impact:** Prevented passing database-loaded `TemplateVersion` bytes into the specialized generator.

### Root Cause 4: Lack of Server-Side Pre-Enqueue Validation
- **File:** `backend/app/api/documents.py`
- **Defect:** `POST /api/v1/documents` accepted arbitrary JSON dictionaries and immediately returned `202 Accepted` without verifying:
  1. Whether `template_id` was provided.
  2. Whether the template existed in the library or database.
  3. Whether the template was in `approved` status.
  4. Whether a compatible document renderer was registered for that template.
  5. Whether the input data satisfied the template's schema.
- **Impact:** Invalid or draft requests were enqueued, clogging the background worker and failing asynchronously rather than failing fast at the HTTP boundary with RFC 9457 error details.

### Root Cause 5: Worker Exception Classification Flaw
- **File:** `backend/app/worker.py`
- **Defect:** `classify_job_exception` did not categorize `SpikeGenerationError` (or verification gate failures) as non-transient.
- **Impact:** Deterministic document verification failures were classified as transient `GENERATION_ERROR`, causing the worker to retry failed jobs 3 times with 5-minute backoff delays before marking them dead, delaying user feedback.

---

## 3. Corrective Measures Summary

1. **DocumentRenderer Architecture:** Implemented `DocumentRenderer` protocol and `RendererRegistry` in `backend/app/generation/renderers.py`. Both filesystem templates and database byte streams now route through `PlotSaleDeedMarathiRenderer`.
2. **`spike_engine.py` Enhancement:** Added `template_bytes: bytes | None = None` support to `generate_plot_sale_deed_docx`.
3. **Pre-Enqueue Gate:** Added fail-closed validation in `POST /api/v1/documents`: returns 422 for missing/invalid payloads, 404 for unknown templates, and 409 for unapproved/unsupported templates.
4. **Worker Hardening:** Classified `SpikeGenerationError` as `VALIDATION_FAILED` (non-transient), providing immediate failure status without spurious retry storms.
5. **Frontend Badges & Selection:** Updated `TemplateSelectorModal.tsx` and `TemplateLibraryView.tsx` to dynamically query status (`has_renderer`, `can_generate`), show genuine status badges (`Approved`, `Draft`, `Under Review`, `Retired`), and disable generation for draft templates with clear explanatory messages.
