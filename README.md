# job-market-etl

![CI](https://github.com/iamamirhossein/job-market-etl/actions/workflows/ci.yml/badge.svg)

A data pipeline that collects job postings from public APIs, cleans and
enriches them with pandas, stores them in layers, and serves skill and salary
analytics through a FastAPI service.

> **Status:** work in progress...

## Planned architecture

```
Adzuna / Remotive APIs
        │
        ▼
 raw JSON  (bronze, MinIO)
        │  pandas + pandera
        ▼
 clean Parquet  (silver)
        │  DuckDB + dbt
        ▼
 analytics tables  (gold)
        │
        ▼
 FastAPI endpoints  +  Streamlit dashboard
```

Orchestrated daily with Airflow. Runs locally with Docker Compose.

## Tech stack

Python 3.13 · FastAPI · pydantic-settings · pandas · DuckDB · dbt · Airflow ·
Docker Compose · GitHub Actions · uv · ruff · mypy · pytest

## Quick start

### With Docker

```bash
cp .env.example .env      # optional, defaults work without it
docker compose up --build
curl localhost:8585/health
```

API docs (Swagger UI): http://localhost:8585/docs

### Local development

Requires [uv](https://docs.astral.sh/uv/).

```bash
make install    # dependencies + git hooks
make run        # API with auto-reload on port 8585
make check      # lint, type check, tests (same as CI)
```

Run `make help` for all commands.

## Configuration

Settings are read from environment variables or a `.env` file.

| Variable      | Default          | Description                              |
| ------------- | ---------------- | ---------------------------------------- |
| `APP_NAME`    | `job-market-etl` | Name shown in the API docs and logs      |
| `APP_VERSION` | `0.1.0`          | Version shown in the API docs and health |
| `ENVIRONMENT` | `local`          | `local`, `test` or `prod`                |
| `LOG_LEVEL`   | `INFO`           | `DEBUG`, `INFO`, `WARNING` or `ERROR`    |

## Project layout

```
app/
  api/        FastAPI routers
  core/       settings and logging
  schemas/    pydantic response models
tests/        pytest suite
```

## Roadmap

- [x] Project foundation: settings, logging, health endpoint, tests
- [x] Tooling: ruff, strict mypy, pre-commit, Makefile
- [x] Docker image and Compose file, GitHub Actions CI
- [ ] Data extraction from job APIs
- [ ] Cleaning, skill extraction and validation
- [ ] Warehouse loading and dbt models
- [ ] Analytics API and dashboard
- [ ] Airflow orchestration
