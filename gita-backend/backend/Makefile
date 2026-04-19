# Run from `backend/`. Requires https://docs.astral.sh/uv/
#
# Common targets:
#   make sync              # install deps (creates .venv, respects .python-version)
#   make run / test / …
#
# Override uv binary: make sync UV=/path/to/uv

UV ?= uv

.PHONY: sync install run test load-sample-data build-embeddings dev

# Alias for muscle memory after pip-era docs
install: sync

## API + Next.js (script lives next to backend/: ../scripts/dev.sh)
dev:
	@bash ../scripts/dev.sh

sync:
	$(UV) sync

run:
	$(UV) run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

test:
	$(UV) run pytest -q

load-sample-data:
	$(UV) run python scripts/seed_database.py

build-embeddings:
	$(UV) run python scripts/embed_verses.py
