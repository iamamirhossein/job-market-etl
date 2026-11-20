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
  raw JSON  (bronze, S3-compatible object storage)
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

### Running an extraction

With the lake running (`docker compose up -d lake`):

```bash
make extract SOURCE=remotive      # same, source chosen explicitly
uv run python -m pipeline.run_extractor remotive --run-id test-001
```

Each run stores the untouched API response at
`bronze/source=<source>/dt=<date>/<run_id>.json` and logs how many postings
passed the data contract and how many were rejected. Using the same `--run-id`
again overwrites the same object, so re-running is safe.

Run `make help` for all commands.

## Configuration

Settings are read from environment variables or a `.env` file.

| Variable            | Default                 | Description                                  |
| ------------------- | ----------------------- | -------------------------------------------- |
| `APP_NAME`          | `job-market-etl`        | Name shown in the API docs and logs          |
| `APP_VERSION`       | `0.1.0`                 | Version shown in the API docs and health     |
| `ENVIRONMENT`       | `local`                 | `local`, `test` or `prod`                    |
| `LOG_LEVEL`         | `INFO`                  | `DEBUG`, `INFO`, `WARNING` or `ERROR`        |
| `LOG_FORMAT`        | `text`                  | `text` for humans, `json` for log tooling    |
| `LAKE_ENDPOINT_URL` | `http://localhost:9000` | S3-compatible endpoint of the data lake      |
| `LAKE_ACCESS_KEY`   | `lakeadmin`             | Lake access key                              |
| `LAKE_SECRET_KEY`   | `lakeadmin-secret`      | Lake secret key (local development only)     |
| `LAKE_BUCKET`       | `job-market-lake`       | Bucket for bronze, silver and gold data      |

## Health checks

| Endpoint            | Purpose                                                             |
| ------------------- | ------------------------------------------------------------------- |
| `GET /health`       | Liveness: the process is running                                    |
| `GET /health/ready` | Readiness: dependencies work (200), or the lake is unreachable (503) |

The data lake is [RustFS](https://github.com/rustfs/rustfs), an S3-compatible
object store, so the same code runs against AWS S3 in production. Its console
is at http://localhost:9001/rustfs/console/ when running with Docker.

## Data sources

| Source | Access | Notes |
| ------ | ------ | ----- |
| [Remotive](https://remotive.com) | Public API, no key | Small curated feed (about 15 remote jobs), delayed by 24 hours |

Job data is provided by [Remotive](https://remotive.com), and every posting
keeps a link back to its original page on remotive.com. Postings are only used
for analytics in this project and are not republished.

## Project layout

```
app/
  api/        FastAPI routers and dependencies
  core/       settings and logging
  schemas/    pydantic response models
pipeline/
  extract/    source extractors (Remotive) and their base class
  lake/       S3 client and bronze key conventions
  models.py   JobPost data contract
  run_extractor.py   fetch, store raw data in bronze, parse
tests/        pytest suite
```

## Roadmap

- [x] Project foundation: settings, logging, health endpoint, tests
- [x] Tooling: ruff, strict mypy, pre-commit, Makefile
- [x] Docker image and Compose file, GitHub Actions CI
- [x] Object-storage lake, data contract, readiness checks, JSON logging
- [x] Remotive extractor: raw data to bronze, validated `JobPost` objects
- [ ] Adzuna extractor
- [ ] Cleaning, skill extraction and validation
- [ ] Warehouse loading and dbt models
- [ ] Analytics API and dashboard
- [ ] Airflow orchestration
