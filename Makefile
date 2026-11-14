.PHONY: help install run test lint format typecheck check up down logs

PORT ?= 8585

help:
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

install:
	uv sync
	uv run pre-commit install

run:
	uv run uvicorn app.main:app --reload --port $(PORT)

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff check --fix .
	uv run ruff format .

typecheck:
	uv run mypy

check: lint typecheck test

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api
