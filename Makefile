.PHONY: setup dev check test test-golden test-property test-mutation test-coverage migrate seed e2e clean

setup:
	python3.12 -m venv .venv && . .venv/bin/activate && pip install -e "backend[dev]" && cd frontend && npm install

dev:
	docker compose -f deploy/docker-compose.dev.yml up -d db

check:
	. .venv/bin/activate && cd backend && ruff check . && ruff format --check . && mypy --strict app && lint-imports && pytest -q -m "not slow" --cov=app --cov-fail-under=85 && cd ../frontend && npm run lint && npx tsc --noEmit

test:
	. .venv/bin/activate && cd backend && pytest -q

test-golden:
	. .venv/bin/activate && cd backend && pytest -q tests/golden -m "golden"

test-property:
	. .venv/bin/activate && cd backend && pytest -q -m "property"

test-mutation:
	. .venv/bin/activate && cd backend && python scripts/run_mutation_gate.py --min-score 80.0

test-coverage:
	. .venv/bin/activate && cd backend && pytest -q --cov=app --cov-report=term-missing --cov-fail-under=85

migrate:
	. .venv/bin/activate && cd backend && alembic upgrade head

seed:
	. .venv/bin/activate && cd backend && python scripts/seed_dev.py

e2e:
	cd frontend && npx playwright test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

