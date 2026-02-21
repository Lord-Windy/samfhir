# Phase 1: Infrastructure + Skeleton API

## Goal

A deployed, reachable FastAPI server at `api.projectptah.com` with Redis
connected and stub endpoints returning mock data. No FHIR integration yet.

---

## Manual Steps (You)

These require human action — GCP console, domain registrar, and Epic portal.
Complete them before or alongside the automated implementation.

### 1. GCP Project Setup

1. Create a GCP project (e.g., `samfhir` or `projectptah`)
2. Link a billing account to the project
3. Enable the following APIs:
   - Cloud Run Admin API
   - Artifact Registry API
   - Cloud DNS API
   - Serverless VPC Access API (for the VPC Connector)
   - Redis (Memorystore) API
   - Cloud Resource Manager API
4. Install the `gcloud` CLI and authenticate:
   ```bash
   gcloud auth login
   gcloud config set project samfhir
   gcloud auth application-default login   # for Terraform
   ```

### 2. Terraform State Bucket

Create the GCS bucket for Terraform remote state (this must exist before
`terraform init`):

```bash
gcloud storage buckets create gs://samfhir-tfstate \
  --project=samfhir \
  --location=australia-southeast1 \
  --uniform-bucket-level-access
```

### 3. Domain DNS Migration

1. In the GCP Console → Cloud DNS, note the nameservers that Terraform creates
   for the `projectptah.com` managed zone (they'll appear in `terraform output`)
2. Go to your current domain registrar for `projectptah.com`
3. Replace the existing nameservers with the four GCP nameservers
4. DNS propagation can take up to 48 hours (usually much faster)

> **Tip**: You can run `terraform apply` for just the DNS zone first to get the
> nameservers early, then migrate while building the rest.

### 4. Artifact Registry Repository

Create a Docker repository for container images:

```bash
gcloud artifacts repositories create samfhir \
  --repository-format=docker \
  --location=australia-southeast1 \
  --description="SamFHIR container images"
```

Configure Docker authentication:

```bash
gcloud auth configure-docker australia-southeast1-docker.pkg.dev
```

### 5. Epic FHIR App Registration (Phase 2 Prep)

Not required for Phase 1, but register early since approval can take time:

1. Go to [fhir.epic.com](https://fhir.epic.com/) and create an account
2. Register a new application:
   - **Application name**: SamFHIR
   - **Redirect URI**: `https://api.projectptah.com/smart/callback`
   - **FHIR version**: R4
   - **Resources**: Patient, Observation, Condition, MedicationRequest,
     AllergyIntolerance
3. Save the **Non-Production Client ID** — you'll need it in Phase 2

---

## Implementation Plan

### Step 1: Python Project Scaffolding

Create the project structure and configure tooling.

**Files to create:**

```
backend/
├── pyproject.toml
├── Dockerfile
├── src/
│   └── samfhir/
│       ├── __init__.py
│       ├── main.py
│       └── config.py
```

**`pyproject.toml`** — project metadata and dependencies:

| Dependency          | Purpose                                |
| ------------------- | -------------------------------------- |
| `fastapi`           | Web framework                          |
| `uvicorn[standard]` | ASGI server                            |
| `pydantic-settings` | Typed config from env vars             |
| `redis[hiredis]`    | Async Redis client with C parser       |
| `httpx`             | Async HTTP client (for FHIR calls later) |
| `fhir.resources`    | FHIR R4 Pydantic models (Phase 2)     |
| `fhirpy`            | Async FHIR client (Phase 2)           |
| `authlib`           | OAuth2/PKCE (Phase 2)                 |

Dev dependencies:

| Dependency        | Purpose                     |
| ----------------- | --------------------------- |
| `pytest`          | Test runner                 |
| `pytest-asyncio`  | Async test support          |
| `httpx`           | Test client for FastAPI     |
| `ruff`            | Linting + formatting        |

**`config.py`** — `pydantic-settings` reading from `SAMFHIR_`-prefixed env vars:

- `app_name`, `debug`, `host`, `port`
- `redis_url` (default: `redis://localhost:6379/0`)
- `fhir_base_url`, `smart_client_id`, `smart_redirect_uri`, `smart_scopes`
- `cors_origins`

**`main.py`** — FastAPI app entrypoint. Wires routers, lifespan (Redis
connect/disconnect), CORS middleware.

### Step 2: Domain Layer

The core — no framework imports allowed here.

**Files to create:**

```
backend/src/samfhir/domain/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── patient.py        # Patient, PatientSummary
│   └── observation.py    # Observation, Condition, Medication, Allergy
├── ports/
│   ├── __init__.py
│   ├── fhir_port.py      # FhirPort ABC
│   └── cache_port.py     # CachePort ABC
└── services/
    ├── __init__.py
    └── patient_service.py
```

**Domain models** — frozen dataclasses:

- `Patient`: id, family_name, given_name, birth_date, gender
- `PatientSummary`: patient + active_conditions, recent_observations,
  active_medications, allergies
- `Condition`: id, code, display, clinical_status, onset_date
- `Observation`: id, code, display, value, unit, effective_date
- `Medication`: id, code, display, status, authored_on
- `Allergy`: id, code, display, clinical_status, criticality

**Port interfaces** — ABCs:

- `FhirPort`: get_patient, get_patient_summary, search_conditions,
  search_observations, search_medications, search_allergies
- `CachePort`: get, set, delete, flush, stats

**`patient_service.py`** — orchestrates FhirPort and CachePort. Implements the
cache-aside pattern: check cache → miss → call FHIR → store in cache → return.

### Step 3: Outbound Adapters

**Files to create:**

```
backend/src/samfhir/adapters/
├── __init__.py
├── outbound/
│   ├── __init__.py
│   ├── stub_fhir_client.py   # Implements FhirPort with hardcoded data
│   └── redis_cache.py        # Implements CachePort with redis.asyncio
```

**`stub_fhir_client.py`** — returns hardcoded mock data for Jason Argonaut
(Epic's test patient). This lets the full API work end-to-end without Epic. Will
be swapped for `epic_fhir_client.py` in Phase 2.

**`redis_cache.py`** — implements CachePort using `redis.asyncio`:

- `get` / `set` (with TTL) / `delete` / `flush`
- `stats` — track hit/miss counts (use Redis `INCR` on counter keys)
- Connection health check method for the health endpoint

### Step 4: Inbound Adapters (API Routers)

**Files to create:**

```
backend/src/samfhir/adapters/
├── inbound/
│   ├── __init__.py
│   └── api/
│       ├── __init__.py
│       ├── health_router.py
│       ├── patient_router.py
│       ├── fhir_router.py
│       └── schemas/
│           ├── __init__.py
│           └── patient_schemas.py
```

**Endpoints:**

| Method | Path                                 | Router         | Description                    |
| ------ | ------------------------------------ | -------------- | ------------------------------ |
| GET    | `/health`                            | health_router  | Status + Redis connectivity    |
| GET    | `/health/ready`                      | health_router  | Readiness probe for Cloud Run  |
| GET    | `/api/v1/patients/{id}`              | patient_router | Get patient by ID              |
| GET    | `/api/v1/patients/{id}/summary`      | patient_router | Aggregated patient summary     |
| GET    | `/api/v1/patients/{id}/conditions`   | patient_router | Patient conditions             |
| GET    | `/api/v1/patients/{id}/observations` | patient_router | Patient observations           |
| GET    | `/api/v1/patients/{id}/medications`  | patient_router | Patient medications            |
| GET    | `/api/v1/patients/{id}/allergies`    | patient_router | Patient allergies              |
| GET    | `/api/v1/cache/stats`                | fhir_router    | Cache hit/miss statistics      |
| DELETE | `/api/v1/cache`                      | fhir_router    | Flush cache (dev/debug)        |

**Response schemas** (`patient_schemas.py`) — Pydantic models for API
responses. These are DTOs, separate from domain models.

### Step 5: Dependency Wiring

**File to create:**

```
backend/src/samfhir/dependencies.py
```

FastAPI's `Depends()` composition root. Provides:

- `get_settings` → `Settings` singleton
- `get_redis` → Redis connection (from app lifespan state)
- `get_cache` → `RedisCacheAdapter` (depends on `get_redis`)
- `get_fhir_client` → `StubFhirClient` (swapped to EpicFhirClient in Phase 2)
- `get_patient_service` → `PatientService` (depends on `get_fhir_client` +
  `get_cache`)

### Step 6: Docker + Local Dev

**Files to create:**

```
backend/Dockerfile
docker-compose.yml      # at repo root
```

**`Dockerfile`** — multi-stage build:

1. **Builder stage**: `python:3.12-slim` + `uv`, install dependencies
2. **Runtime stage**: `python:3.12-slim`, copy installed packages, run uvicorn

**`docker-compose.yml`**:

- `api` service: builds from `backend/Dockerfile`, port 8000, env vars
- `redis` service: `redis:7-alpine`, port 6379

### Step 7: Terraform Infrastructure

**Files to create:**

```
terraform/
├── main.tf              # Provider, backend config
├── variables.tf         # Input variables
├── outputs.tf           # Nameservers, Cloud Run URL
├── cloud_run.tf         # Cloud Run service
├── redis.tf             # Memorystore Redis
├── dns.tf               # Cloud DNS zone + records
├── networking.tf        # VPC, subnet, VPC Connector
└── terraform.tfvars.example
```

**Resources provisioned:**

| Resource                | Config                                          |
| ----------------------- | ----------------------------------------------- |
| Cloud Run service       | `samfhir-api`, port 8000, min 0 / max 3         |
| Memorystore Redis       | Basic tier, 1GB, private IP only                |
| VPC Connector           | Cloud Run → Redis via private network           |
| Cloud DNS managed zone  | `projectptah.com`                               |
| DNS CNAME record        | `api.projectptah.com` → Cloud Run URL           |
| Artifact Registry       | Referenced (created manually, see Manual Steps) |

**`terraform.tfvars.example`**:

```hcl
project_id = "samfhir"
region     = "australia-southeast1"
domain     = "projectptah.com"
```

**Outputs**: nameservers (for manual DNS migration), Cloud Run URL, Redis host.

### Step 8: Makefile

**File to create:**

```
Makefile     # at repo root
```

**Targets:**

| Target   | Command                                           |
| -------- | ------------------------------------------------- |
| `dev`    | `docker compose up --build`                       |
| `test`   | `cd backend && uv run pytest`                     |
| `lint`   | `cd backend && uv run ruff check .`               |
| `format` | `cd backend && uv run ruff format .`              |
| `build`  | `docker build -t samfhir-api backend/`            |
| `deploy` | Build, push to Artifact Registry, deploy to Cloud Run |

### Step 9: Tests

**Files to create:**

```
backend/tests/
├── conftest.py
├── unit/
│   └── domain/
│       └── test_patient_service.py
└── integration/
    ├── test_patient_router.py
    └── test_redis_cache.py
```

**`conftest.py`** — shared fixtures:

- `mock_fhir_port`: stub FhirPort for unit tests
- `mock_cache_port`: in-memory CachePort for unit tests
- `test_client`: `httpx.AsyncClient` bound to the FastAPI app with stub adapters

**Unit tests** (`test_patient_service.py`):

- Patient service returns patient from FhirPort
- Patient summary aggregates data from multiple FhirPort calls
- Cache-aside pattern: cache hit skips FhirPort call
- Cache-aside pattern: cache miss calls FhirPort then stores result

**Integration tests** (`test_patient_router.py`):

- Health endpoint returns `{"status": "ok", "redis": "connected"}`
- Patient endpoint returns well-formed JSON matching schema
- Cache stats endpoint reflects hits after repeated requests
- Cache flush endpoint clears cached data

**Integration tests** (`test_redis_cache.py`):

- Set/get round-trip
- TTL expiry
- Delete removes key
- Stats track hits and misses

> Redis integration tests require a running Redis instance. Use
> `docker compose up redis` or `testcontainers` for CI.

---

## Acceptance Criteria

- [ ] `terraform apply` provisions all GCP resources without errors
- [ ] `https://api.projectptah.com/health` returns
      `{"status": "ok", "redis": "connected"}`
- [ ] All stub endpoints return well-formed JSON matching their schema
- [ ] Cache stats endpoint shows hits/misses after repeated calls to stub
      endpoints
- [ ] `make test` passes
- [ ] `make lint` passes with zero warnings

---

## Key Decisions

| Decision               | Choice              | Rationale                                                 |
| ---------------------- | -------------------- | --------------------------------------------------------- |
| Cloud provider         | GCP                  | Cloud Run scale-to-zero saves cost for a temp project     |
| Python package manager | `uv`                 | Fast, correct, replaces pip/pip-tools/virtualenv          |
| Project structure      | `src/` layout        | Prevents accidental imports from the project root         |
| Config management      | `pydantic-settings`  | Env vars → typed Python objects with validation           |
| Stub data              | Hardcoded in adapter | Swapped out in Phase 2 — domain layer doesn't change      |
| Redis client           | `redis.asyncio`      | Official async client, no need for deprecated `aioredis`  |

---

## Implementation Order

```
Manual Steps (can start immediately, run in parallel)
  │
  ▼
Step 1: Project scaffolding (pyproject.toml, config, main.py)
  │
  ▼
Step 2: Domain layer (models, ports, services)
  │
  ▼
Step 3: Outbound adapters (stub FHIR client, Redis cache)
  │
  ▼
Step 4: Inbound adapters (API routers, response schemas)
  │
  ▼
Step 5: Dependency wiring (dependencies.py)
  │
  ▼
Step 6: Docker + local dev (Dockerfile, docker-compose.yml)
  │
  ▼
Step 7: Terraform (infra as code)
  │
  ▼
Step 8: Makefile
  │
  ▼
Step 9: Tests
  │
  ▼
Deploy + verify acceptance criteria
```
