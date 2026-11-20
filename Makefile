.PHONY: help install run test lint format typecheck check up down logs

PORT ?= 8585

extract: ## Extract jobs into the lake (SOURCE=remotive)
	uv run python -m pipeline.run_extractor $(SOURCE)

help:
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

install: ## Install dependencies and git hooks
	uv sync
	uv run pre-commit install

run: ## Run the API locally with reload
	uv run uvicorn app.main:app --reload --port $(PORT)

test: ## Run tests
	uv run pytest

lint: ## Check lint and formatting
	uv run ruff check .
	uv run ruff format --check .

format: ## Auto-fix lint issues and format code
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Run mypy
	uv run mypy

check: lint typecheck test ## Run every check (same as CI)

up: ## Start the stack in Docker
	docker compose up -d --build

down: ## Stop the Docker stack
	docker compose down

logs: ## Follow API container logs
	docker compose logs -f api
