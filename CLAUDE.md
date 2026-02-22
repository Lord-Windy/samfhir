# SamFHIR

FHIR R4 patient data viewer — FastAPI backend with hexagonal architecture, Redis caching, React frontend.

## Quick Reference

```bash
# Local dev (FastAPI + Redis via Docker)
docker compose up --build

# Tests (unit + integration; Redis integration tests skip if Redis unavailable)
cd backend && uv run pytest

# Lint / format
cd backend && uv run ruff check .
cd backend && uv run ruff format .

# Build & deploy
make build
make deploy
```

## Environment Variables

All config uses the `SAMFHIR_` prefix (via pydantic-settings):
- `SAMFHIR_REDIS_URL` — Redis connection string (default: `redis://localhost:6379/0`)
- `SAMFHIR_FHIR_BASE_URL` — FHIR server base URL (default: `http://hapi.fhir.org/baseR4`)
- `SAMFHIR_DEBUG` — Enable debug mode (default: `false`)

## Project Structure

- `backend/src/samfhir/domain/` — Domain models, port interfaces (ABCs), services. No framework imports.
- `backend/src/samfhir/adapters/inbound/api/` — FastAPI routers and response schemas.
- `backend/src/samfhir/adapters/outbound/` — FHIR client and Redis cache implementations.
- `backend/src/samfhir/dependencies.py` — FastAPI Depends() composition root.
- `terraform/` — GCP infrastructure (Cloud Run, Memorystore Redis, VPC, DNS).

## Architecture

Hexagonal (ports & adapters). Dependencies point inward. Domain layer knows nothing about FastAPI, Redis, or FHIR wire formats.
