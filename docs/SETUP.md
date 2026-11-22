# SETUP.md: local development, step by step

Target: a working dev environment in about 60-90 minutes. Written for Windows 11 with WSL2 (recommended), also works on macOS and Linux. Commands are for a Bash shell.

---

## 1. Prerequisites

| Tool | Version | Why |
|---|---|---|
| Git | recent | Version control |
| Python | 3.12 | Backend |
| Node.js | 22 LTS (or current LTS) | Frontend, `getdesign` |
| Docker Desktop (or Docker Engine) | recent | PostgreSQL, optional converter |
| LibreOffice | 7.x or newer | PDF conversion (local dev) |
| make | any | Task shortcuts |
| Microsoft Word | 2016+ | **Required** to check template output manually |
| Antigravity IDE | current | Your agentic IDE (or any editor + agent) |

**Windows:** install WSL2 and Ubuntu (`wsl --install`), enable Docker Desktop's WSL integration, and work **inside the WSL file system** (`~/projects/lekhan`), not under `C:\`. Docker bind mounts on `C:\` are slow.

### Fonts
Install on your machine **and** in WSL/Docker image: Inter, JetBrains Mono, Noto Sans Devanagari, Noto Serif Devanagari. Install the company's licensed Kruti Dev font on your Windows machine only if you need to open original samples; never commit font files.

---

## 2. Create the repository and docs

```bash
mkdir -p ~/projects/lekhan && cd ~/projects/lekhan
git init -b main
# copy the generated docs into the repo root:
#   README.md  AGENTS.md  DESIGN.md  docs/*.md  docs/reference/starbucks-DESIGN.upstream.md
```

If you want to regenerate the design reference yourself:
```bash
npx getdesign@latest add starbucks        # writes DESIGN.md in the current folder
mv DESIGN.md docs/reference/starbucks-DESIGN.upstream.md
# then use the project-specific DESIGN.md provided with these docs at the repo root
```

Create `.gitignore` entries **before the first commit**:
```
.env
.env.*
!.env.example
samples-private/
work/
*.docx
!templates-library/**/*.docx
*.pdf
node_modules/
.venv/
__pycache__/
```
(`samples-private/` is where the company's archive lives; it must never be committed.)

---

## 3. Backend

```bash
cd ~/projects/lekhan
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
mkdir -p backend && cd backend
```
Create `backend/pyproject.toml` with the dependencies (pin exact versions after the first successful install):

```toml
[project]
name = "lekhan-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi", "uvicorn[standard]", "pydantic>=2", "pydantic-settings",
  "sqlalchemy>=2", "alembic", "psycopg[binary]",
  "docxtpl", "python-docx", "defusedxml", "regex", "argon2-cffi",
  "itsdangerous", "httpx", "structlog", "python-multipart", "cryptography",
]
[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "hypothesis", "mypy", "ruff", "import-linter",
       "schemathesis", "bandit", "pip-audit", "mutmut"]
```
Install:
```bash
pip install -e ".[dev]"
pip freeze > requirements.lock        # then review versions and licences
```

### Environment file
```bash
cp .env.example .env                  # create .env.example first (names only)
```
`.env.example`:
```
ENV=dev
DATABASE_URL=postgresql+psycopg://lekhan:lekhan@localhost:5432/lekhan_dev
SECRET_KEY=change-me
MASTER_KEY=change-me-base64
INDEX_KEY=change-me-base64
STORAGE_PATH=./var/storage
SOFFICE_BIN=soffice
ALLOWED_ORIGINS=http://localhost:5173
SESSION_IDLE_MINUTES=30
SESSION_ABSOLUTE_HOURS=12
```
Generate real random values for the three keys:
```bash
python - <<'EOF'
import secrets, base64
print("SECRET_KEY=", secrets.token_urlsafe(48))
print("MASTER_KEY=", base64.b64encode(secrets.token_bytes(32)).decode())
print("INDEX_KEY=", base64.b64encode(secrets.token_bytes(32)).decode())
EOF
```
Paste into `.env`. **Never commit `.env`.**

---

## 4. Database (Docker)

`deploy/docker-compose.dev.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: lekhan
      POSTGRES_PASSWORD: lekhan
      POSTGRES_DB: lekhan_dev
    ports: ["5432:5432"]
    volumes: ["lekhan_pg:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U lekhan -d lekhan_dev"]
      interval: 5s
      retries: 10
volumes:
  lekhan_pg:
```
Run:
```bash
docker compose -f deploy/docker-compose.dev.yml up -d db
docker compose -f deploy/docker-compose.dev.yml exec db psql -U lekhan -d lekhan_dev -c "CREATE EXTENSION IF NOT EXISTS pg_trgm; CREATE EXTENSION IF NOT EXISTS btree_gist; CREATE EXTENSION IF NOT EXISTS pgcrypto;"
```
Migrations and synthetic data (once these scripts exist, per PLAN.md week 4-6):
```bash
make migrate
make seed
```

---

## 5. Frontend

```bash
cd ~/projects/lekhan
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install tailwindcss @tailwindcss/vite react-hook-form zod @hookform/resolvers \
  @tanstack/react-query react-i18next i18next react-router-dom
npm install -D vitest @testing-library/react @testing-library/jest-dom playwright eslint
```
Then: apply the tokens and Tailwind mapping from `DESIGN.md` (sections 2 and 9), add the fonts, and create `src/i18n/en.json` and `mr.json`. Configure the Vite dev proxy so `/api` goes to `http://localhost:8000` (this avoids cookie and CORS problems in development).

---

## 6. Run everything

```bash
# terminal 1 (backend)
source .venv/bin/activate
cd backend && uvicorn app.main:app --reload --port 8000

# terminal 2 (worker)
cd backend && python -m app.worker

# terminal 3 (frontend)
cd frontend && npm run dev          # http://localhost:5173
```
Checks: `http://localhost:8000/health/live` returns OK; `http://localhost:8000/api/docs` (dev only) shows the OpenAPI UI.

### Makefile (root) minimal version
```make
setup:   ; python3.12 -m venv .venv && . .venv/bin/activate && pip install -e "backend[dev]" && cd frontend && npm install
dev:     ; docker compose -f deploy/docker-compose.dev.yml up -d db
check:   ; . .venv/bin/activate && cd backend && ruff check . && mypy --strict app && lint-imports && pytest -q -m "not slow" && cd ../frontend && npm run lint && npx tsc --noEmit
test:    ; . .venv/bin/activate && cd backend && pytest -q
migrate: ; . .venv/bin/activate && cd backend && alembic upgrade head
seed:    ; . .venv/bin/activate && cd backend && python scripts/seed_dev.py
e2e:     ; cd frontend && npx playwright test
```

---

## 7. Check LibreOffice and fonts

```bash
soffice --version
fc-list | grep -i "Noto Sans Devanagari"      # fonts visible on Linux/WSL
cd /tmp && soffice --headless --convert-to pdf --outdir /tmp/out /path/to/synthetic.docx
```
If the PDF shows boxes instead of Marathi letters, install the Devanagari fonts in WSL (`sudo apt install fonts-noto-core` or the specific Noto packages) and run `fc-cache -f`.

---

## 8. Antigravity setup

1. Open the repository folder (`~/projects/lekhan`, via WSL remote on Windows).
2. Confirm `AGENTS.md` is at the root. Antigravity reads it in addition to `GEMINI.md`; if you add a `GEMINI.md`, it takes precedence. Enable nested `AGENTS.md` loading in Settings if you add subfolder files. If your version expects rules in `.agent/rules/` (or `.agents/rules/`), put short rule files there that point to `AGENTS.md`.
3. Set the review policy so that terminal commands and MCP writes **ask for approval**. Do not use "always proceed".
4. Use **Planning** mode for anything touching auth, migrations, templates, or encryption; **Fast** mode for small edits.
5. Add MCP servers following `docs/MCP.md` (read-only dev DB, GitHub, Playwright, your local corpus-tools).
6. Create saved workflows (`.agent/workflows/`): `/add-endpoint` (updates API.md, test matrix), `/add-template-test`, `/new-migration`, `/explain-back`.
7. First prompt to try: "Read AGENTS.md, docs/PRD.md and docs/ARCHITECTURE.md. Propose a plan for week 4 (backend core). Do not write code yet."

---

## 9. The private sample archive

```bash
mkdir -p ~/projects/lekhan/samples-private      # git-ignored
# place the company's archive here, outside version control, encrypted disk recommended
```
Rules: never commit it, never paste it into chat, never point an agent at it; use the local `corpus_tools` CLI and the corpus-tools MCP server, which return counts and redacted summaries only. Delete the archive after templates are extracted, or per the data agreement.

---

## 10. Pre-commit hooks (recommended)
`.pre-commit-config.yaml` with: ruff, ruff-format, mypy, eslint, a **secrets scanner** (for example `gitleaks`), and a project hook that runs the PII/leftover scanner on staged files.
```bash
pip install pre-commit && pre-commit install
```

---

## 11. Troubleshooting

| Problem | Fix |
|---|---|
| `psycopg` cannot connect | Container not healthy yet; check `docker compose ps`; confirm port 5432 not used by a local Postgres |
| `alembic` cannot find models | Run from `backend/`; set `PYTHONPATH=.` |
| Slow Docker on Windows | Keep the repo inside WSL, not `C:\` |
| Marathi shows as boxes in PDF | Install Noto Devanagari fonts, `fc-cache -f` |
| Cookies not stored in dev | Use the Vite proxy; do not call the API on another origin; `Secure` cookies need HTTPS (use a dev flag only in `ENV=dev`) |
| `soffice` hangs | Use a unique `-env:UserInstallation` per run; kill stray `soffice` processes |
| Word says the output needs repair | See `docs/DEBUGGING.md` section 2.1 |
| `npx getdesign` fails | Check network/proxy; it only writes a `DESIGN.md` file in the current folder |

## 12. First-day checklist
- [ ] Repo created, `.gitignore` in place, no secrets or samples committed
- [ ] Python and Node environments installed; `make check` runs (even if tests are empty)
- [ ] Postgres container healthy with extensions
- [ ] `AGENTS.md` loaded by Antigravity; review policy set to ask
- [ ] Design tokens applied; Marathi and English fonts render correctly in a test page
- [ ] LibreOffice converts a synthetic DOCX containing Marathi text to PDF correctly
- [ ] You can open a generated DOCX in Microsoft Word without a repair prompt
