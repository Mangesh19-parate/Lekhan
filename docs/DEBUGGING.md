# DEBUGGING.md

Method first, then playbooks for the problems this project will actually have.

---

## 1. Method (use every time)
1. **Reproduce** with synthetic data. If you cannot reproduce, you cannot fix it. Never debug with real client data.
2. **Get the correlation id** from the error toast or response. Search logs by it: API, job, converter.
3. **Shrink** the input until the bug is as small as possible (one party, one clause, one paragraph).
4. **Form one hypothesis, test one thing.** Write it down in `docs/journal.md`.
5. **Write the failing test** before the fix; keep it after.
6. **Fix the cause, not the symptom;** then ask "what lint, test, or check would have caught this?" and add it.
7. If an agent is helping: give it the **error, the code, and logs with personal data removed**. Never paste `.env`, tokens, or sample deeds.

### Logs and tools
```bash
docker compose logs -f api worker            # structured JSON logs
docker compose exec db psql -U lekhan -d lekhan_dev
make logs-job JOB=<job_id>                   # prints job row + related log lines
python -m app.cli reproduce --document <id>  # regenerates from stored snapshot into /tmp
```
Inspect a DOCX: `unzip -o file.docx -d /tmp/x && python -m xml.dom.minidom /tmp/x/word/document.xml | less`.

---

## 2. DOCX problems

### 2.1 Word shows "unreadable content, repair?"
Likely causes and checks:
1. Unescaped `&`, `<` in rendered values (use the renderer's escaping; test with `Tom & Co`).
2. Invalid XML from a bad tag replacement (find with `xmllint --noout word/document.xml`).
3. Duplicate or missing relationship ids after editing headers/footers.
4. A field code (`PAGE`) inserted without begin/separate/end characters.
5. Output assembled from two different templates' parts.
**Do:** run the DOCX validator; diff `word/document.xml` of the template and the output; bisect by removing sections from the template.

### 2.2 Tags are not replaced, or `{{ ... }}` remains
Word splits text into runs (the median sample file has over 1,000). A tag spread over several runs will not render.
**Do:** run the lint's split-run check; merge adjacent runs with identical formatting; retype the tag in plain text in one go; avoid mid-tag spell-check or formatting changes. The verification gate should have blocked this; if it did not, add a test.

### 2.3 Repeated rows or numbering wrong
- Typed numbers ("1)") left in the template: replace with generated numbering.
- Loop tags placed outside the table row. Put `{%tr for ... %}` in the row, not the paragraph.
- Off-by-one after removing a party: check list indexes start at 1 only in presentation, not data.

### 2.4 Page numbers show "…. 2 ….", or repeat
Typed page numbers were not converted to fields. Replace with PAGE fields in the footer; confirm the footer is linked correctly for sections 2+.

### 2.5 Layout differs from the original
Expected after the font change. Compare with the parity images; adjust font size, line spacing, tab stops; record accepted deviations. Differences between Word and PDF come from font substitution on the server (section 4.2).

### 2.6 Output opens but is "Compatibility Mode" or loses styles
The template came from a `.doc` conversion. Re-save once through the conversion tool with the target format and check styles; prefer clean `.docx` sources.

---

## 3. Devanagari and Unicode

### 3.1 Boxes, question marks or wrong shapes
Font missing or lacks Devanagari glyphs. Check the template font report; install the chosen font on the server and the desktop; set both ASCII and complex-script (`w:cs`) fonts in styles.

### 3.2 Broken conjuncts, matras in the wrong place
1. Negative letter-spacing on Devanagari in CSS (UI): set `letter-spacing: 0` for `:lang(mr), :lang(hi)`.
2. Text sliced by code points (use grapheme clusters, `regex` `\X`).
3. Missing normalisation: normalise to NFC at input boundaries.
4. ZWJ/ZWNJ stripped by a sanitiser: allow U+200C and U+200D in Devanagari fields.

### 3.3 Search does not find a name
Marathi has no Postgres stemmer. Use trigram search; normalise both sides (NFC, strip honorifics); check the GIN index is used (`EXPLAIN`).

### 3.4 Digits wrong (Devanagari vs Western)
Check the template's digits setting and the tenant default; the language pack's `to_digits` must be applied once, at render time only.

---

## 4. Kruti Dev conversion

### 4.1 Output is garbage in one line only
Latin text typed under a Kruti font (PAN, Aadhaar, cheque numbers, amounts). Check the run's font; the detector should have flagged it. Fix the source run's font or add it to the review queue.

### 4.2 Conjuncts or matras misordered ("sarvhe" style errors)
Likely reordering or half-form bug. Reproduce with the smallest raw string, add it to the synthetic fixtures, fix the rule, run the round-trip suite and confirm no regressions.

### 4.3 Different results for the same word in two files
Different Kruti variants (010, 021, 030, 050, 100, 111, DevLys). Check the run's font name and the mapping table used.

### 4.4 Round-trip score dropped
Bisect by commit; list changed file ids; check whether a mapping order changed (order of replacements matters).

---

## 5. Generation jobs and PDF

| Symptom | Check | Fix |
|---|---|---|
| Job stuck in `running` | `locked_at` older than timeout; worker crashed | Janitor requeues; inspect worker logs; ensure handler is idempotent |
| Duplicate documents | Missing `Idempotency-Key` or unique constraint | Enforce header; unique `(tenant_id, idempotency_key)` |
| PDF conversion timeouts | LibreOffice profile lock; huge document; missing fonts | Unique `-env:UserInstallation` per run; kill process group; raise timeout only after finding the cause |
| Zombie `soffice` processes | Timeout without killing group | Kill by process group; add a reaper; add a test |
| Output missing though job `succeeded` | Atomic rename failed; storage path wrong | Verify `output_hash` path exists; reconcile job with storage |
| Gaps in document numbers | Counter updated outside the document transaction | Keep both in one transaction; run the concurrency test |
| Verification gate rejects output | Leftover tags, empty required field, page range | Read the gate message; reproduce from snapshot with `app.cli reproduce` |

---

## 6. Auth, tenancy and security bugs

| Symptom | Likely cause |
|---|---|
| `401` after a short time | Idle timeout; cookie not sent (SameSite/Secure mismatch in dev) |
| `403` on every POST | Missing or stale `X-CSRF-Token` (re-fetch `/auth/me`) |
| User sees another user's document | Missing owner check in `authorize()`; fix and add a regression test immediately |
| Cross-tenant data appears | Query without `tenant_id`; add the filter; consider enabling RLS earlier |
| Login works locally, fails on server | Cookie `Secure` without HTTPS; reverse proxy not passing `X-Forwarded-Proto` |
| Personal data in logs | A debug `print` or exception message including data; scrub, rotate if secrets, add a log-scrubbing test |

**If real personal data reaches the repo or logs:** stop, remove from history (`git filter-repo`), rotate any secret, notify the company, add a scanner rule.

---

## 7. Database

| Symptom | Check |
|---|---|
| Slow search | `EXPLAIN (ANALYZE, BUFFERS)`; is the GIN trigram index used? Is the expression identical to the index expression? |
| Lock waits on numbering | Long transaction around document creation; shorten it |
| Migration fails in CI | Run on empty DB and on previous fixture; check expand/contract ordering |
| Deadlocks | Consistent lock ordering; keep transactions short; retry on `40P01` |
| Connection errors under load | Pool size vs `max_connections`; leaked sessions |
| Snapshot JSON mismatches schema | Validate with Pydantic on write; migrate snapshots with explicit versioned upgraders |

---

## 8. Frontend

| Symptom | Check |
|---|---|
| Form shows a field that should be hidden | Condition not re-evaluated; the validate endpoint response differs from the client's assumptions; check conformance vectors |
| Marathi text overflows button | Fixed widths; use min-width and wrapping |
| Repeater loses data on remove | Keys by index instead of stable id |
| Draft lost on refresh | Autosave debounce failed; ephemeral store TTL; check network tab |
| Double submit creates two jobs | Disable button on submit; send `Idempotency-Key` per user action |
| CORS or cookie errors in dev | Origin mismatch; use the Vite proxy so the app and API share an origin |

---

## 9. Performance
1. Measure first: logs show durations per pipeline stage.
2. Typical order of culprits: LibreOffice start-up, fonts, large DOCX with thousands of runs (merge runs at template approval), unindexed JSONB queries, N+1 queries.
3. Cache compiled templates by `(template_version_id, checksum)`; do not cache rendered documents.
4. Re-run the benchmark after each change and note the numbers in `docs/benchmarks.md`.

---

## 10. Incident checklist (production)
1. **Stabilise:** stop the bleeding (disable the feature flag, pause the worker, roll back).
2. **Communicate:** tell the company what is affected, what is not, next update time.
3. **Preserve evidence:** logs, job rows, audit entries; do not delete.
4. **Fix:** smallest safe change with a test; deploy to staging first if time allows.
5. **Verify:** run golden tests and a Word-open check on affected templates.
6. **Post-incident note** within 48 hours: timeline, cause, fix, prevention, and the test or check you added. If a wrong clause reached a signed document, involve the lawyer immediately.

## 11. When stuck for more than 90 minutes
Write the problem in five lines (expected, actual, what you tried, smallest reproduction, logs without personal data) and ask: the agent, then a peer or forum, then the company's technical contact. Writing it down solves a third of problems by itself.
