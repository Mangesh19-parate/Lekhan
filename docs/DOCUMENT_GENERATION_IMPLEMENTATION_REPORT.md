# Document Generation Implementation Report

**Project:** Lekhan (Multilingual Property Legal Drafting Platform)  
**Author:** Principal Backend Engineer & Software Architect  
**Date:** November 25, 2026  
**Status:** Implemented & Verified  

---

## 1. Architectural Overview

To resolve the document generation failures, the generation pipeline was restructured to decouple template resolution, rendering strategy, output verification, and persistence into clear, single-responsibility components.

```
┌──────────────────────────────────────────────────────────────┐
│                    API Gateway / FastAPI                     │
│  POST /api/v1/documents                                      │
│  - Fail-closed pre-enqueue validation (404/409/422)          │
│  - Idempotency deduplication via Idempotency-Key             │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 PostgreSQL Job Queue                         │
│  - Status: queued, State: REQUESTED                          │
│  - Transactional claiming: FOR UPDATE SKIP LOCKED            │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Background Worker Process                   │
│  - run_worker_once(visibility_timeout=300s, max_attempts=3)  │
│  - Non-transient exception classification                    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                   GenerationPipelineFSM                      │
│  REQUESTED -> VALIDATED -> RENDERED -> VERIFIED -> STORED    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                 RendererRegistry & Renderers                 │
│  - PlotSaleDeedMarathiRenderer (sale_deed_plot_mr)           │
│    * Normalizes flat / nested / repeater facts               │
│    * Computes honorifics, Marathi numbers-to-words           │
│    * Formats sellers, purchasers, payment blocks             │
│    * Injects document.xml into DOCX archive                  │
│  - ManifestDrivenDocxRenderer (generic approved templates)   │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                  Output Verification Gate                    │
│  - Reopen DOCX archive via zipfile                           │
│  - Verify word/document.xml is present and non-empty         │
│  - Assert zero unrendered {{...}} or {%...%} tags            │
│  - Stamp customXml/provenance.xml cryptographic receipt      │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────┐
│             Persistent Storage & Audit History               │
│  - Atomic write: storage.put(documents/{tenant}/{id}.docx)   │
│  - Verify written file exists in object store                │
│  - Sequential gap-free document number (DOC/YYYY/NNNNN)      │
│  - Immutable GeneratedDocumentRecord in Postgres             │
│  - Audit log entry: document_generated                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. Key Components Implemented

### 2.1 Explicit DocumentRenderer Protocol & Registry
**Path:** `backend/app/generation/renderers.py`

- **`DocumentRenderer` Protocol:**
  ```python
  class DocumentRenderer(Protocol):
      def can_render(self, template_id: str) -> bool: ...
      def render(
          self,
          template_id: str,
          payload: dict[str, Any],
          template_bytes: bytes | None = None,
      ) -> bytes: ...
  ```

- **`PlotSaleDeedMarathiRenderer`:**
  - Registered for `sale_deed_plot_mr`.
  - Normalizes both nested structures and dotted flat form inputs (`property.mouza`, `financial.total_consideration`, etc.).
  - Handles repeaters for `sellers`, `purchasers`, `instalments`, and `witnesses`.
  - Accepts both filesystem templates and database `TemplateVersion` bytes, eliminating the previous bypass bug.
  - Generates Marathi honorifics, currency in words (`number_to_words_mr`), area conversions (`sqm_to_sqft`), and payment clauses.

- **`ManifestDrivenDocxRenderer`:**
  - Fallback generic renderer for manifest-driven templates with sandboxed Jinja2 (`StrictUndefined`).

- **`RendererRegistry`:**
  - Singleton registry (`default_renderer_registry`) enabling clean, priority-based renderer lookup:
    ```python
    renderer = default_renderer_registry.get_renderer(template_id)
    ```

### 2.2 Template Engine Byte Stream Support
**Path:** `backend/app/generation/spike_engine.py`

Updated `generate_plot_sale_deed_docx`:
```python
def generate_plot_sale_deed_docx(
    data: PlotSaleDeedInput,
    template_path: Path | None = None,
    template_bytes: bytes | None = None,
) -> bytes:
```
When `template_bytes` is provided, `io.BytesIO(template_bytes)` is used directly as the input zipfile stream, preserving template version immutability.

### 2.3 Server-Side Pre-Enqueue Validation Gate
**Path:** `backend/app/api/documents.py`

Enforces fail-closed validation on `POST /api/v1/documents`:
1. `template_id` must be present (422 Unprocessable Content).
2. Template must exist in library or database (404 Not Found).
3. Template status must be `"approved"` (409 Conflict with RFC 9457 error message).
4. Template must have a registered renderer (409 Conflict).

### 2.4 Output Verification Gate Hardening
**Path:** `backend/app/generation/pipeline.py`

Before transitioning to `STORED`, the pipeline executes an output verification gate:
1. Reopens the generated DOCX as a zipfile.
2. Asserts `word/document.xml` exists and is non-empty.
3. Scans all XML parts (`word/*.xml`) for any unrendered Jinja tags (`{{...}}` or `{%...%}`).
4. Stamps cryptographic provenance metadata into `customXml/provenance.xml`.
5. Performs atomic storage write and immediately verifies that `storage.exists(storage_key)` is `True`.

### 2.5 Template Discovery API & Frontend Badges
**Paths:**
- `backend/app/api/templates_admin.py`
- `frontend/src/features/form_engine/TemplateSelectorModal.tsx`
- `frontend/src/features/templates/TemplateLibraryView.tsx`

1. **Backend Discovery:** Added `has_renderer: bool` and `can_generate: bool` fields to `TemplateSummary`.
2. **Accurate Badging:**
   - `"approved"` -> `<Badge variant="approved" label="Approved" />`
   - `"under_review"` -> `<Badge variant="under_review" label="Under Review" />`
   - `"retired"` -> `<Badge variant="danger" label="Retired" />`
   - `"draft"` -> `<Badge variant="draft" label="Draft" />`
3. **Disabled Draft Generation:** Templates that are not approved or lack renderers are dimmed in `TemplateSelectorModal.tsx`, disallow drafting clicks, and display: *"Draft template — Generation disabled until officially approved."*
