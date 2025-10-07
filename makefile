.PHONY: lint format

lint:
	uv run ruff check src/

format:
	uv run black src/
