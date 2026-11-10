# Workflow: /add-template-test

When adding a template test:
1. Ensure synthetic fixture data only (fictional names, invalid-by-construction IDs).
2. Cover all Marathi grammar variations: 1 male, 1 female, 2 male, 2 female, mixed, 3+ parties.
3. Verify no split tags `{{` or `{%` remain in the output DOCX.
4. Verify PAGE footer fields are present and no page numbers are hardcoded/typed.
5. Save golden file in `backend/tests/fixtures/golden/`.

