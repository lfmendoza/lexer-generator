.PHONY: install test lint format typecheck

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -q

lint:
	ruff check src tests yalex_cli.py

format:
	ruff format src tests yalex_cli.py

typecheck:
	mypy src/yalex

check: lint typecheck test
