.PHONY: install run test lint typecheck check clean

install:  ## Install dependencies (including dev)
	uv sync --extra dev

run:  ## Launch the web UI
	uv run datapm-studio

test:  ## Run tests
	uv run pytest

lint:  ## Format and lint
	uv run ruff format .
	uv run ruff check .

typecheck:  ## Run type checker
	uv run pyright datapm_studio/

check: lint typecheck test  ## Run lint + typecheck + tests

clean:  ## Remove caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	rm -rf .ruff_cache
