# SamFHIR

FHIR R4 patient data viewer. Search patients, view demographics, conditions, observations, medications, and allergies from any FHIR R4 server.

Built with FastAPI, React, and Redis. Deployed on Google Cloud Run.

## Features

- **Patient search** by name or direct ID lookup
- **Clinical dashboard** with tabbed views for conditions, observations, medications, and allergies
- **Observation recording** via a create form
- **Redis caching** with 5-minute TTL and cache stats monitoring
- **Health checks** with Redis connectivity status

## Architecture

Hexagonal (ports & adapters). The domain layer defines abstract ports for FHIR access and caching. Adapters implement those ports for HAPI FHIR and Redis. Dependencies point inward -- the domain knows nothing about FastAPI, Redis, or FHIR wire formats.

```
frontend/          React 19 + TypeScript, Vite, Tailwind CSS, shadcn/ui, React Query
backend/           FastAPI, fhirpy, Redis, pydantic-settings
terraform/         GCP Cloud Run, Memorystore Redis, VPC, DNS
```

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

This starts the API on `localhost:8000` and Redis on `localhost:6379`. The frontend is bundled into the backend container and served at the root.

### Local Development

**Backend:**

```bash
cd backend
uv sync
uv run uvicorn samfhir.main:app --reload
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server runs on `localhost:5173` and proxies `/api` and `/health` to the backend.

## Testing

```bash
# Backend (unit + integration)
make test

# Frontend (Vitest + React Testing Library)
make frontend-test

# Both
make test-all
```

Backend integration tests that require Redis will skip automatically if Redis is unavailable. Tests marked `@pytest.mark.live` run against a real HAPI FHIR server.

## Linting

```bash
make lint           # Backend (ruff)
make frontend-lint  # Frontend (eslint)
make lint-all       # Both
```

## Configuration

Environment variables use the `SAMFHIR_` prefix (via pydantic-settings):

| Variable | Default | Description |
|----------|---------|-------------|
| `SAMFHIR_FHIR_BASE_URL` | `http://hapi.fhir.org/baseR4` | FHIR server base URL |
| `SAMFHIR_REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SAMFHIR_DEBUG` | `false` | Enable debug mode |
| `SAMFHIR_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/patients?name=` | Search patients |
| GET | `/api/v1/patients/{id}` | Get patient |
| GET | `/api/v1/patients/{id}/summary` | Patient summary with clinical data |
| GET | `/api/v1/patients/{id}/conditions` | Conditions |
| GET | `/api/v1/patients/{id}/observations` | Observations |
| GET | `/api/v1/patients/{id}/medications` | Medications |
| GET | `/api/v1/patients/{id}/allergies` | Allergies |
| POST | `/api/v1/observations` | Create observation |
| POST | `/api/v1/conditions` | Create condition |
| GET | `/api/v1/cache/stats` | Cache statistics |
| DELETE | `/api/v1/cache` | Flush cache |
| GET | `/health` | Health check |
| GET | `/health/ready` | Readiness probe |

## Deploy

Deployed to GCP Cloud Run with Memorystore Redis via Terraform.

```bash
make build    # Build Docker image
make deploy   # Build, push to Artifact Registry, deploy to Cloud Run
```

Infrastructure is defined in `terraform/` and targets `australia-southeast1`.

## Tech Stack

**Backend:** Python 3.12+, FastAPI, fhirpy, Redis, pydantic-settings, httpx

**Frontend:** React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4, shadcn/ui, TanStack React Query, React Router 7

**Testing:** pytest + pytest-asyncio (backend), Vitest + React Testing Library + MSW (frontend)

**Infrastructure:** Docker, Google Cloud Run, Memorystore Redis, Terraform

## Open Questions

- Investigate API partner response times, and why observations take so long to propagate through

## License

Apache 2.0 -- see [LICENSE](LICENSE).
