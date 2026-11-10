# Lekhan (working title)

Multilingual **property legal drafting** web app for a Nagpur/Vidarbha document practice. Enter the facts of a transaction once; generate an editable, properly formatted **Marathi or English** deed (Hindi later) from the company's approved templates, with a review trail and a portal-ready data sheet.

> **Status:** planning complete; implementation starts at Week 1 of a 26-week plan (see `docs/PLAN.md`).
> **Important:** generated documents are **drafts**. They must be reviewed by a qualified professional before execution or registration. This software does not provide legal advice and never states that a document is legally valid.

---

## Why this exists
The company drafts deeds by copying old, filled-in Word documents. Most Marathi and Hindi files use the legacy **Kruti Dev** font (not Unicode), page numbers and numbering are typed by hand, and the same details are retyped into a government registration portal. Lekhan replaces that with structured data, Unicode templates, automatic numbering, leftover-data checks and audit.

## What it does (6-month release)
- Wizard: language, property type, document type
- Dynamic forms with repeaters (parties, instalments, witnesses, boundaries)
- Marathi and English DOCX generation from approved, versioned templates
- Amount in words, dates, area conversions
- Leftover-data lint, template lifecycle, document review workflow
- History, automatic document numbering, audit log
- Party/property reuse, search, portal data-entry sheet (should-have)

Not in this release: Hindi templates, Kruti Dev export, fee calculator, duplicate detection, document comparison, multi-tenant operation, AI drafting. See `docs/FEATURES.md`.

## Stack
React + TypeScript + Vite + Tailwind (design from `DESIGN.md`) | FastAPI + SQLAlchemy 2 + Alembic | PostgreSQL 16 | docxtpl | LibreOffice (PDF) | Docker Compose + Caddy | pytest, Hypothesis, Playwright



## Quick start 

```bash
git clone <your-repo> lekhan && cd lekhan
make setup                       # venv, backend deps, frontend deps
cp backend/.env.example backend/.env   # then fill real random keys (never commit)
docker compose -f deploy/docker-compose.dev.yml up -d db
make migrate && make seed        # synthetic data only
make dev                         # database up; then start API, worker and Vite (see SETUP.md)
make check                       # lint, types, tests
```
Open `http://localhost:5173`.

## Repository layout
```
AGENTS.md  DESIGN.md  README.md
backend/        FastAPI app, domain modules, tests, migrations
frontend/       React app (features, shared, i18n)
corpus_tools/   Offline developer CLI: convert, scan, cluster (not shipped)
templates-library/  Approved templates + manifests (synthetic or redacted only)
conformance/    Shared DSL test vectors
docs/           Documentation and ADRs
deploy/         Docker Compose, Caddy, backup scripts
samples-private/   (git-ignored) the company's archive, never committed
```

## Principles
1. **No real personal data** in the repository, tests, logs, screenshots or chat.
2. **Templates are legal artefacts:** versioned, immutable once approved, signed off by the company's lawyer.
3. **Marathi first, English equal;** Hindi designed for, built later.
4. **DOCX is the master;** PDF is a convenience copy.
5. **Correct before clever:** no `eval`, no floats for money, no silent transliteration, no auto-approval of converted text.

## Contributing / workflow
Branch per task, Conventional Commits, small pull requests, tests with every change, `make check` green, explain-back note in the PR. Agent and human contributors follow `AGENTS.md`.

## Security
Report issues privately to the maintainer. See `docs/AUTH.md` for the threat model. Never include personal data in reports.

## Licence and ownership
To be agreed with the company in writing (code, templates, data ownership; maintenance terms). Placeholder: proprietary, all rights reserved.

## Credits
Design inspired by the Starbucks reference generated with `getdesign` (VoltAgent `awesome-design-md`). No Starbucks brand assets are used.
