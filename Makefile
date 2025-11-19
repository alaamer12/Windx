.PHONY: help install dev run test lint format type-check clean migrate-create migrate-up migrate-down docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make dev            - Install with dev dependencies"
	@echo "  make run            - Run development server"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make format         - Format code with ruff"
	@echo "  make type-check     - Type check with mypy"
	@echo "  make clean          - Clean cache and build files"
	@echo "  make migrate-create - Create new migration"
	@echo "  make migrate-up     - Apply migrations"
	@echo "  make migrate-down   - Rollback migration"
	@echo "  make docker-up      - Start Docker services"
	@echo "  make docker-down    - Stop Docker services"

install:
	uv sync

dev:
	uv sync --extra dev

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .

format:
	uv run ruff format .

type-check:
	uv run mypy app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf build dist *.egg-info htmlcov

migrate-create:
	@read -p "Enter migration message: " msg; \
	uv run alembic revision --autogenerate -m "$$msg"

migrate-up:
	uv run alembic upgrade head

migrate-down:
	uv run alembic downgrade -1

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down
