# SamFHIR - Technical Requirements Document

## Overview

SamFHIR is a demonstration project that integrates with Epic's FHIR sandbox
(fhir.epic.com) using the SMART on FHIR authorization framework. It showcases
competency in healthcare interoperability standards through a Python FastAPI
backend, Redis caching layer, and a React/TypeScript frontend — all deployed to
GCP via Terraform under the domain `projectptah.com`.

**Target audience for this TRD**: A Java/Rust developer. Python idioms and
architectural decisions are spelled out explicitly.

---

## Technology Stack

| Layer            | Technology                              | Why                                                                                          |
| ---------------- | --------------------------------------- | -------------------------------------------------------------------------------------------- |
| Language         | Python 3.12+                            | Required by brief. Type hints used everywhere — closest to typed-language comfort.            |
| Web Framework    | FastAPI                                 | Async-native, Pydantic-based request/response validation, auto-generated OpenAPI docs.       |
| FHIR Models      | `fhir.resources` (Pydantic v2)          | Type-safe FHIR R4 data models. Pairs naturally with FastAPI's Pydantic foundation.           |
| FHIR Client      | `fhirpy` (async)                        | Async FHIR CRUD client with chainable search. No auth baked in — we control that ourselves.  |
| OAuth/SMART      | `authlib` + `httpx`                     | Manual SMART on FHIR flow. Gives full control of the authorization code + PKCE exchange.     |
| Cache            | Redis 7 via `redis.asyncio`             | Async Redis client. Caches FHIR responses to reduce round-trips to Epic.                    |
| Frontend         | React 18 + TypeScript + Vite            | Modern SPA tooling. Vite for fast builds.                                                    |
| Infrastructure   | Terraform + GCP                         | Cloud Run (scale-to-zero, built-in HTTPS), Memorystore Redis, Cloud DNS.                    |
| Containers       | Docker                                  | Single Dockerfile for the FastAPI app. Frontend served as static assets via Cloud Run or CDN. |
| Testing          | `pytest` + `pytest-asyncio` + `httpx`   | `pytest` is Python's standard. `httpx.AsyncClient` for testing FastAPI without a live server. |
| Linting/Format   | `ruff`                                  | Single tool for both linting and formatting. Fast (written in Rust — you'll appreciate that). |
| Dependency Mgmt  | `uv`                                    | Fast Python package manager (also Rust-based). Replaces pip, pip-tools, and virtualenv.      |

---

## Architecture

### Hexagonal Architecture in Python

In Java you'd use packages and interfaces. Python's equivalent:

- **Ports** = Abstract Base Classes (ABCs) defined in the domain layer. These are
  Python's version of Java interfaces. They use `abc.ABC` and `@abstractmethod`.
- **Adapters** = Concrete implementations that live in their own package and import
  the port they satisfy.
- **Dependency Injection** = FastAPI's built-in `Depends()` system. It's
  constructor injection via function parameters — similar to Spring's `@Autowired`
  but explicit and testable.

```
Think of it as:
  Java Interface        → Python ABC (abstract base class)
  @Repository impl      → adapter/outbound/redis_cache.py (implements CachePort)
  @Service              → domain/services/patient_service.py (depends on ports)
  @RestController       → adapter/inbound/api/patient_router.py (FastAPI router)
  Spring @Autowired     → FastAPI Depends()
```

### Dependency Rule

Dependencies point inward. The domain layer knows nothing about FastAPI, Redis,
or FHIR wire formats. It operates on domain models and ports.

```
┌──────────────────────────────────────────────────────────────┐
│                    Inbound Adapters                          │
│  (FastAPI routers, request/response DTOs)                    │
├──────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│  (Use cases / service orchestration)                         │
├──────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│  (Domain models, port interfaces, business logic)            │
├──────────────────────────────────────────────────────────────┤
│                    Outbound Adapters                         │
│  (FHIR client, Redis cache, OAuth client)                    │
└──────────────────────────────────────────────────────────────┘
```

### Project Layout

```
samfhir/
├── terraform/                    # Phase 1: Infrastructure as code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── cloud_run.tf
│   ├── redis.tf
│   ├── dns.tf
│   ├── networking.tf
│   └── terraform.tfvars.example
│
├── backend/                      # Python FastAPI application
│   ├── pyproject.toml            # Project metadata + dependencies (like Cargo.toml / pom.xml)
│   ├── uv.lock                   # Lockfile (like Cargo.lock)
│   ├── Dockerfile
│   │
│   ├── src/
│   │   └── samfhir/              # Root Python package
│   │       ├── __init__.py       # Every directory needs this to be a Python package
│   │       ├── main.py           # FastAPI app entrypoint (wires everything together)
│   │       ├── config.py         # Settings via pydantic-settings (env vars → typed config)
│   │       │
│   │       ├── domain/           # ── THE CORE ── No framework imports here
│   │       │   ├── __init__.py
│   │       │   ├── models/       # Domain entities (plain Python dataclasses or Pydantic)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── patient.py
│   │       │   │   └── observation.py
│   │       │   ├── ports/        # Abstract interfaces (ABCs)
│   │       │   │   ├── __init__.py
│   │       │   │   ├── fhir_port.py       # Port for FHIR server interactions
│   │       │   │   └── cache_port.py      # Port for cache interactions
│   │       │   └── services/     # Domain services (business logic)
│   │       │       ├── __init__.py
│   │       │       └── patient_service.py
│   │       │
│   │       ├── adapters/         # ── IMPLEMENTATIONS ──
│   │       │   ├── __init__.py
│   │       │   ├── inbound/      # Driving adapters (things that call us)
│   │       │   │   ├── __init__.py
│   │       │   │   └── api/      # FastAPI routers
│   │       │   │       ├── __init__.py
│   │       │   │       ├── health_router.py
│   │       │   │       ├── patient_router.py
│   │       │   │       ├── fhir_router.py
│   │       │   │       └── schemas/         # Request/Response DTOs (Pydantic models)
│   │       │   │           ├── __init__.py
│   │       │   │           └── patient_schemas.py
│   │       │   └── outbound/     # Driven adapters (things we call)
│   │       │       ├── __init__.py
│   │       │       ├── epic_fhir_client.py  # Implements FhirPort using fhirpy
│   │       │       ├── redis_cache.py       # Implements CachePort using redis.asyncio
│   │       │       └── smart_auth.py        # SMART on FHIR OAuth2 flow
│   │       │
│   │       └── dependencies.py   # FastAPI Depends() wiring (the "composition root")
│   │
│   └── tests/
│       ├── conftest.py            # Shared fixtures (like @BeforeEach in JUnit)
│       ├── unit/
│       │   └── domain/
│       │       └── test_patient_service.py
│       └── integration/
│           ├── test_patient_router.py
│           └── test_redis_cache.py
│
├── frontend/                     # Phase 3: React + TypeScript
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       ├── api/                  # API client (calls our FastAPI backend)
│       ├── components/
│       ├── hooks/
│       ├── pages/
│       └── types/                # TypeScript types mirroring FHIR resources
│
├── Dockerfile                    # Multi-stage: build frontend, serve via FastAPI
├── docker-compose.yml            # Local dev: FastAPI + Redis
├── Makefile                      # Common commands (dev, test, lint, deploy)
└── CLAUDE.md                     # Project instructions for Claude Code
```

### Key Python Concepts for a Java/Rust Developer

| Concept                    | Java/Rust Equivalent              | Python Way                                                                                         |
| -------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------- |
| `pyproject.toml`           | `pom.xml` / `Cargo.toml`         | Single file for project metadata, dependencies, tool config.                                       |
| `__init__.py`              | (implicit in Java packages)       | Required in every directory to make it a Python package. Can be empty.                             |
| `abc.ABC` + `@abstractmethod` | `interface` / `trait`         | How you define a port. Subclasses must implement all abstract methods.                             |
| `@dataclass`               | Record / struct                   | Immutable data holder. Use `frozen=True` for true immutability.                                   |
| `Pydantic BaseModel`       | (no direct equivalent)            | Like `@dataclass` but with runtime validation, JSON serialization, and schema generation.         |
| `async def` / `await`      | `CompletableFuture` / `async/.await` | Python's async is single-threaded (like Rust's tokio with 1 worker). FastAPI handles the event loop. |
| `Depends()`                | `@Autowired` / (manual in Rust)   | FastAPI's DI. Declare dependencies as function parameters. Resolved per-request.                  |
| `conftest.py`              | `@BeforeAll` / test fixtures      | Shared test setup. Fixtures defined here are auto-discovered by pytest.                           |
| Type hints                 | Types / Types                     | Optional at runtime but enforced by `mypy`/`pyright`. Always use them.                            |
| Virtual environment        | (classpath) / (cargo manages)     | Isolated Python installation per project. `uv` creates and manages this for you.                   |

---

## Infrastructure (GCP via Terraform)

### Why GCP Over AWS

For a temporary demo project that runs for a week or two:

- **Cloud Run**: Scale-to-zero (no cost when idle), built-in HTTPS, no ALB/NAT
  Gateway costs. Fargate would cost ~$30/month minimum just for networking.
- **Memorystore Redis**: Basic tier, 1GB — ~$7/month.
- **Cloud DNS**: ~$0.20/month per zone.
- **Estimated total**: ~$15–25/month vs ~$50–80/month on AWS.

### Resources

```
Internet
   │
   ▼
Cloud DNS (projectptah.com)
   │
   ▼
Cloud Run (samfhir-api)          ◄── Built-in HTTPS + managed cert
   │  port 8000
   │
   ├──► Memorystore Redis        ◄── via VPC Connector, port 6379
   │    (private, no public IP)
   │
   └──► Epic FHIR Sandbox        ◄── outbound HTTPS to fhir.epic.com
        (external)
```

### DNS Setup

Terraform will create a Cloud DNS managed zone for `projectptah.com`. You will
need to update the domain's nameservers at your registrar to point to the GCP
nameservers that Terraform outputs. This is a one-time manual step.

```hcl
# dns.tf (simplified)
resource "google_dns_managed_zone" "projectptah" {
  name     = "projectptah"
  dns_name = "projectptah.com."
}

resource "google_dns_record_set" "api" {
  name         = "api.projectptah.com."
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.projectptah.name
  rrdatas      = [google_cloud_run_v2_service.api.uri]
}
```

### Terraform State

State stored in a GCS bucket (created manually once before `terraform init`):

```hcl
terraform {
  backend "gcs" {
    bucket = "samfhir-tfstate"
    prefix = "terraform/state"
  }
}
```

---

## SMART on FHIR Integration

### Epic Sandbox Details

| Item                  | Value                                                                          |
| --------------------- | ------------------------------------------------------------------------------ |
| FHIR Base URL (R4)    | `https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4`                   |
| Authorize Endpoint    | `https://fhir.epic.com/interconnect-fhir-oauth/oauth2/authorize`               |
| Token Endpoint        | `https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token`                   |
| SMART Config          | `{base}/.well-known/smart-configuration`                                       |
| Test User             | `fhirjason` / `epicepic1` (selects patient "Jason Argonaut")                   |
| Alternative Test User | `ARGONAUT` / `ARGONAUT`                                                        |

### Authorization Flow (Standalone Launch)

We implement the **Standalone Launch** flow because our app is accessed directly
by a user (not launched from within an EHR).

```
┌──────────┐     1. GET /smart/launch          ┌──────────────┐
│  Browser  │ ──────────────────────────────►  │  Our FastAPI  │
│           │                                   │  Backend      │
│           │  ◄── 2. Redirect to Epic ──────  │               │
│           │      authorize endpoint           │               │
│           │      (with PKCE challenge)        │               │
│           │                                   │               │
│           │     3. User logs in at Epic       │               │
│           │     4. Epic redirects to          │               │
│           │        /smart/callback            │               │
│           │ ──────────────────────────────►   │               │
│           │                                   │  5. Exchange  │
│           │                                   │  auth code    │
│           │                                   │  for token    │
│           │                                   │  (with PKCE   │
│           │  ◄── 6. Return patient data ──── │   verifier)   │
└──────────┘                                    └──────────────┘
                                                       │
                                                       │ 5a. POST /oauth2/token
                                                       ▼
                                                ┌──────────────┐
                                                │  Epic FHIR   │
                                                │  Server       │
                                                └──────────────┘
```

### Scopes Requested

```
launch/patient        # Request patient picker (standalone launch)
patient/Patient.rs    # Read + Search Patient resources
patient/Observation.rs
patient/Condition.rs
patient/MedicationRequest.rs
patient/AllergyIntolerance.rs
openid                # OpenID Connect for user identity
fhirUser              # Get the logged-in user as a FHIR resource
```

### PKCE (Proof Key for Code Exchange)

Epic requires PKCE for public clients. This is the same as what you'd see in a
mobile app OAuth flow:

1. Generate a random `code_verifier` (43–128 chars, URL-safe).
2. Compute `code_challenge = BASE64URL(SHA256(code_verifier))`.
3. Send `code_challenge` + `code_challenge_method=S256` in the authorize request.
4. Send `code_verifier` in the token exchange request.

This prevents authorization code interception attacks.

### Token Storage

Access tokens are stored in Redis with the patient context ID as part of the key.
Tokens are short-lived (typically 5 minutes from Epic) so Redis TTL is set to
match `expires_in` from the token response.

```python
# Pseudocode for the token cache
await redis.setex(
    f"token:{patient_id}",
    expires_in,
    json.dumps({"access_token": token, "patient": patient_id})
)
```

---

## Redis Caching Strategy

### What Gets Cached

| Key Pattern                           | Value                        | TTL       | Rationale                                      |
| ------------------------------------- | ---------------------------- | --------- | ---------------------------------------------- |
| `token:{session_id}`                  | OAuth access token + context | 5 min     | Match Epic's token expiry.                     |
| `fhir:patient:{patient_id}`          | Patient resource JSON        | 15 min    | Demographics rarely change mid-session.        |
| `fhir:conditions:{patient_id}`       | Condition bundle JSON        | 10 min    | Problem list is relatively stable.             |
| `fhir:observations:{patient_id}`     | Observation bundle JSON      | 5 min     | Vitals/labs may update more frequently.        |
| `fhir:medications:{patient_id}`      | MedicationRequest bundle     | 10 min    | Medication list changes infrequently.          |
| `fhir:allergies:{patient_id}`        | AllergyIntolerance bundle    | 15 min    | Allergy list is very stable.                   |
| `smart:config`                        | SMART configuration JSON     | 1 hour    | Server metadata changes very rarely.           |

### Cache-Aside Pattern

The standard pattern (you'd recognise this from any caching layer):

```python
async def get_patient(self, patient_id: str) -> Patient:
    # 1. Check cache
    cached = await self.cache.get(f"fhir:patient:{patient_id}")
    if cached:
        return Patient.model_validate_json(cached)

    # 2. Cache miss → fetch from FHIR server
    patient = await self.fhir_client.read("Patient", patient_id)

    # 3. Store in cache
    await self.cache.set(f"fhir:patient:{patient_id}", patient.json(), ttl=900)

    return patient
```

### Why Redis Specifically

Beyond the caching use case, having Redis in the stack demonstrates familiarity
with a technology commonly expected in healthcare backend systems. It also serves
as the backing store for SMART on FHIR session state (tokens, PKCE verifiers,
CSRF state parameters) which must survive across the authorize → callback
redirect cycle.

---

## API Endpoints

### Phase 1 — Stub Endpoints (Pre-Epic Integration)

These return mock/empty responses. The point is to have the routing, validation,
caching infrastructure, and hexagonal wiring all working before Epic is involved.

| Method | Path                          | Description                                       | Returns                 |
| ------ | ----------------------------- | ------------------------------------------------- | ----------------------- |
| GET    | `/health`                     | Health check (includes Redis connectivity)        | `{"status": "ok", "redis": "connected"}` |
| GET    | `/health/ready`               | Readiness probe for Cloud Run                     | `{"ready": true}`       |
| GET    | `/api/v1/patients/{id}`       | Get patient by ID                                 | Stub Patient DTO        |
| GET    | `/api/v1/patients/{id}/summary` | Aggregated patient summary                      | Stub summary DTO        |
| GET    | `/api/v1/patients/{id}/conditions` | Patient's conditions/diagnoses               | Stub Condition list     |
| GET    | `/api/v1/patients/{id}/observations` | Patient's observations (vitals, labs)       | Stub Observation list   |
| GET    | `/api/v1/patients/{id}/medications` | Patient's active medications                | Stub Medication list    |
| GET    | `/api/v1/patients/{id}/allergies` | Patient's allergies                           | Stub Allergy list       |
| GET    | `/api/v1/cache/stats`         | Redis cache hit/miss statistics                   | Cache stats DTO         |
| DELETE | `/api/v1/cache`               | Flush the cache (dev/debug tool)                  | `{"flushed": true}`     |

### Phase 2 — Live FHIR Endpoints (Epic Integration)

Same paths as above, but now backed by real FHIR calls through the hexagonal
ports. Additional endpoints for the SMART on FHIR flow:

| Method | Path                          | Description                                       |
| ------ | ----------------------------- | ------------------------------------------------- |
| GET    | `/smart/launch`               | Initiates SMART standalone launch → redirects to Epic |
| GET    | `/smart/callback`             | OAuth callback from Epic → exchanges code for token |
| GET    | `/smart/status`               | Check if current session has a valid token        |
| POST   | `/api/v1/observations`        | Write an observation back to the sandbox          |
| POST   | `/api/v1/conditions`          | Write a condition back to the sandbox             |

**Writing back to the sandbox** is important to demonstrate — it shows
bidirectional FHIR capability, not just read-only consumption.

### Phase 3 — Frontend-Facing Endpoints

No new backend endpoints needed. The React frontend consumes the Phase 2 API.
Static assets are served by FastAPI's `StaticFiles` mount or a separate Cloud Run
service.

---

## Domain Models

These live in `domain/models/` and have **no dependency** on FHIR wire format,
FastAPI, or Redis. They are our internal representation.

```python
# domain/models/patient.py
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class Patient:
    """Our domain's view of a patient. Not a FHIR Patient resource."""
    id: str
    family_name: str
    given_name: str
    birth_date: date
    gender: str

@dataclass(frozen=True)
class PatientSummary:
    """Aggregated view combining data from multiple FHIR resources."""
    patient: Patient
    active_conditions: list["Condition"]
    recent_observations: list["Observation"]
    active_medications: list["Medication"]
    allergies: list["Allergy"]
```

### Port Interfaces

```python
# domain/ports/fhir_port.py
from abc import ABC, abstractmethod
from samfhir.domain.models.patient import Patient, PatientSummary

class FhirPort(ABC):
    """Port for interacting with a FHIR server. Adapter can be Epic, HAPI, or a mock."""

    @abstractmethod
    async def get_patient(self, patient_id: str) -> Patient:
        ...

    @abstractmethod
    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        ...

    @abstractmethod
    async def search_conditions(self, patient_id: str) -> list[Condition]:
        ...
```

```python
# domain/ports/cache_port.py
from abc import ABC, abstractmethod
from typing import Optional

class CachePort(ABC):
    """Port for cache operations. Adapter can be Redis, in-memory, or no-op."""

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        ...
```

---

## Other FHIR Sandboxes (Stretch Goal)

If Epic integration is complete and there's time, the hexagonal architecture
makes it trivial to swap in other FHIR servers — just write a new adapter
implementing `FhirPort`.

| Sandbox               | URL                                                          | Auth Required | Notes                            |
| --------------------- | ------------------------------------------------------------ | ------------- | -------------------------------- |
| HAPI FHIR (open)      | `http://hapi.fhir.org/baseR4`                                | No            | Read/write, periodically purged. |
| Cerner/Oracle (open)  | `https://fhir-open.cerner.com/r4/ec2458f2-1e24-41c8-b71b-0e701af7583d/` | No            | Read-only.                       |
| Cerner/Oracle (SMART) | `https://fhir.cerner.com/`                                   | Yes           | Full SMART on FHIR.              |

---

## Phase Definitions

---

### Phase 1: Infrastructure + Skeleton API

**Goal**: A deployed, reachable FastAPI server at `api.projectptah.com` with
Redis connected and stub endpoints returning mock data. No FHIR integration yet.

#### Deliverables

1. **Terraform** provisioning:
   - GCP project setup (manual prerequisite: project creation, billing, GCS
     state bucket)
   - Cloud Run service for the FastAPI container
   - Memorystore Redis (Basic tier, 1GB)
   - VPC Connector (Cloud Run → Redis)
   - Cloud DNS managed zone for `projectptah.com`
   - DNS A/CNAME record for `api.projectptah.com` → Cloud Run
   - Manual step: update nameservers at domain registrar to GCP's nameservers

2. **Python project** scaffolding:
   - `pyproject.toml` with all dependencies
   - Hexagonal directory structure as defined above
   - `config.py` with `pydantic-settings` reading from environment variables
   - Domain models (Patient, Condition, Observation, Medication, Allergy)
   - Port interfaces (FhirPort, CachePort)
   - Redis adapter implementing CachePort
   - **Stub FHIR adapter** implementing FhirPort with hardcoded mock data
   - FastAPI routers for all Phase 1 endpoints
   - `dependencies.py` wiring ports to adapters via `Depends()`
   - Health check endpoint that verifies Redis connectivity

3. **Docker** setup:
   - Dockerfile (multi-stage: uv install → slim runtime image)
   - `docker-compose.yml` for local dev (FastAPI + Redis)

4. **CI basics**:
   - `Makefile` with targets: `dev`, `test`, `lint`, `format`, `build`, `deploy`
   - `ruff` configuration in `pyproject.toml`

5. **Tests**:
   - Unit tests for domain services using mock ports
   - Integration test for Redis adapter (using `testcontainers` or a local Redis)
   - Integration test for health endpoint

#### Phase 1 Acceptance Criteria

- [ ] `terraform apply` provisions all GCP resources without errors
- [ ] `https://api.projectptah.com/health` returns `{"status": "ok", "redis": "connected"}`
- [ ] All stub endpoints return well-formed JSON matching their schema
- [ ] Cache stats endpoint shows hits/misses after repeated calls to stub endpoints
- [ ] `make test` passes
- [ ] `make lint` passes with zero warnings

#### Phase 1 Decisions

| Decision                    | Choice               | Rationale                                                  |
| --------------------------- | -------------------- | ---------------------------------------------------------- |
| Cloud provider              | GCP                  | Cloud Run's scale-to-zero saves cost for a temp project.   |
| Python package manager      | `uv`                 | Fast, correct, replaces pip/pip-tools/virtualenv.          |
| Project structure           | `src/` layout        | Prevents accidental imports from the project root.         |
| Config management           | `pydantic-settings`  | Env vars → typed Python objects with validation.           |
| Stub data                   | Hardcoded in adapter | Swapped out in Phase 2 — the domain layer doesn't change.  |
| Redis client                | `redis.asyncio`      | Official Redis async client. No need for `aioredis` (merged). |

---

### Phase 2: SMART on FHIR + Epic Integration

**Goal**: Replace the stub FHIR adapter with a real Epic adapter. Implement the
full SMART on FHIR standalone launch flow. Demonstrate reading from and writing
to the Epic sandbox.

#### Prerequisites

- Phase 1 complete and deployed
- Application registered at [fhir.epic.com](https://fhir.epic.com/) with:
  - Redirect URI: `https://api.projectptah.com/smart/callback`
  - FHIR R4 API access
  - Requested resources: Patient, Observation, Condition, MedicationRequest,
    AllergyIntolerance
  - Non-Production Client ID received

#### Deliverables

1. **SMART on FHIR OAuth2 flow**:
   - `smart_auth.py` adapter handling the full flow:
     - SMART configuration discovery (`.well-known/smart-configuration`)
     - Authorization URL generation with PKCE
     - Callback handler: code → token exchange
     - Token storage in Redis with TTL
     - Token refresh if Epic supports it for the app type
   - State parameter (CSRF) stored in Redis during the authorize → callback cycle
   - PKCE verifier stored in Redis keyed by state parameter

2. **Epic FHIR adapter**:
   - `epic_fhir_client.py` implementing `FhirPort`
   - Uses `fhirpy.AsyncFHIRClient` with the access token from the SMART flow
   - Maps FHIR R4 resources (`fhir.resources.R4B`) to our domain models
   - Caching layer wraps FHIR calls (cache-aside pattern via CachePort)

3. **Write-back endpoints**:
   - `POST /api/v1/observations` — create a simple Observation (e.g., a vital
     sign or a text note) in the Epic sandbox
   - `POST /api/v1/conditions` — create a Condition in the Epic sandbox
   - These demonstrate bidirectional FHIR capability

4. **Session management**:
   - Simple cookie-based session ID (no user authentication — as specified)
   - Session ID maps to the SMART token in Redis
   - If no valid session/token, redirect to `/smart/launch`

5. **Error handling**:
   - Graceful handling of token expiry (re-trigger SMART flow)
   - FHIR OperationOutcome errors mapped to meaningful API responses
   - Rate limiting awareness (Epic has rate limits — back off and retry)

#### Phase 2 Acceptance Criteria

- [ ] Navigating to `/smart/launch` redirects to Epic's authorization page
- [ ] After logging in with `fhirjason`/`epicepic1`, the callback completes and
      a token is stored in Redis
- [ ] `GET /api/v1/patients/{epic_patient_id}` returns real patient data from Epic
- [ ] `GET /api/v1/patients/{id}/summary` aggregates real data from multiple FHIR
      resources
- [ ] `POST /api/v1/observations` successfully creates an observation in the sandbox
- [ ] Cache stats show hits on repeated requests for the same patient
- [ ] Token expiry is handled gracefully (user is redirected to re-authorize)

#### Phase 2 Decisions

| Decision              | Choice                        | Rationale                                                      |
| --------------------- | ----------------------------- | -------------------------------------------------------------- |
| FHIR client library   | `fhirpy` (async)              | Async, clean API, no opinion on auth (we handle that).         |
| FHIR models           | `fhir.resources`              | Pydantic v2 models for validation/serialization of FHIR JSON.  |
| OAuth library         | `authlib` + `httpx`           | Full control. `authlib` handles PKCE generation cleanly.       |
| Session mechanism     | Cookie + Redis                | Simple. No JWT needed since this is a server-rendered flow.    |
| FHIR version          | R4                            | Epic's recommended version. DSTU2 is legacy.                   |

---

### Phase 3: React Frontend

**Goal**: A React/TypeScript SPA that provides a user-friendly interface for
browsing FHIR data and performing actions against the Epic sandbox.

#### Prerequisites

- Phase 2 complete with all live endpoints working
- CORS configured on the FastAPI backend to allow the frontend origin

#### Deliverables

1. **React application** (Vite + TypeScript):
   - Patient dashboard: display demographics, conditions, observations, meds,
     allergies in a clean layout
   - SMART launch trigger: button to initiate the OAuth flow
   - Observation entry form: submit a new observation (e.g., blood pressure, note)
   - Cache statistics view: show cache hit rates and cached keys
   - Connection status indicator: show whether we have a valid FHIR token

2. **API client layer**:
   - Typed API client using `fetch` or a lightweight wrapper
   - TypeScript interfaces mirroring the backend DTOs
   - Error handling with user-friendly messages

3. **Deployment**:
   - Option A: FastAPI serves the built React assets via `StaticFiles` (simplest —
     single Cloud Run service)
   - Option B: Separate Cloud Run service or Cloud CDN for static assets (better
     for production, overkill here)
   - Recommendation: **Option A** for simplicity
   - Multi-stage Dockerfile: build React with Node → copy dist into Python image

4. **UI/UX** (keep it simple):
   - Use a lightweight component library (e.g., Radix UI + Tailwind, or shadcn/ui)
   - Responsive layout but not a design showcase — focus on data display
   - Dark mode not required

#### Phase 3 Acceptance Criteria

- [ ] Frontend loads at `https://projectptah.com` (or `https://app.projectptah.com`)
- [ ] User can click "Connect to Epic" and complete the SMART flow
- [ ] Patient dashboard displays real data from Epic after authentication
- [ ] User can submit a new observation via the form
- [ ] Cache stats are visible in the UI
- [ ] Works in Chrome and Firefox (no IE/Safari testing needed)

#### Phase 3 Decisions

| Decision            | Choice              | Rationale                                               |
| ------------------- | -------------------- | ------------------------------------------------------- |
| Build tool          | Vite                 | Fast, modern, good TypeScript support.                  |
| Component library   | shadcn/ui + Tailwind | Copy-paste components, no heavy dependency.             |
| State management    | React Query (TanStack) | Handles caching, loading states, and refetching for API calls. |
| Routing             | React Router v7      | Standard. Only a few routes needed.                     |
| Serving             | FastAPI `StaticFiles` | Single deployment unit. Simple.                         |

---

## Configuration

All configuration via environment variables, loaded by `pydantic-settings`:

```python
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Server
    app_name: str = "SamFHIR"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # FHIR / SMART
    fhir_base_url: str = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"
    smart_client_id: str = ""
    smart_redirect_uri: str = "http://localhost:8000/smart/callback"
    smart_scopes: str = "launch/patient patient/Patient.rs patient/Observation.rs patient/Condition.rs openid fhirUser"

    # CORS (Phase 3)
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_prefix": "SAMFHIR_"}
```

---

## Testing Strategy

| Layer         | Tool                  | What's Tested                              | FHIR Server Needed? |
| ------------- | --------------------- | ------------------------------------------ | -------------------- |
| Domain        | `pytest`              | Business logic in services                 | No (mocked ports)    |
| Adapters      | `pytest` + `testcontainers` | Redis adapter, FHIR client mapping   | Redis container only |
| API           | `pytest` + `httpx`    | FastAPI endpoints end-to-end               | No (stub adapter)    |
| Integration   | Manual                | Full flow against Epic sandbox             | Yes                  |

```python
# Example: testing the domain service with a mock port
async def test_patient_summary_aggregates_data():
    mock_fhir = MockFhirAdapter(
        patients={"123": Patient(id="123", family_name="Argonaut", ...)},
        conditions={"123": [Condition(id="c1", ...)]},
    )
    mock_cache = MockCacheAdapter()
    service = PatientService(fhir=mock_fhir, cache=mock_cache)

    summary = await service.get_patient_summary("123")

    assert summary.patient.family_name == "Argonaut"
    assert len(summary.active_conditions) == 1
```

---

## Security Notes

- **No user authentication on the API itself** — as specified, this is a
  temporary demo. The SMART on FHIR flow authenticates the *user to Epic*, not
  to our server.
- **HTTPS everywhere** — Cloud Run provides managed TLS. No HTTP.
- **No secrets in code** — all credentials via environment variables / Secret
  Manager.
- **CORS restricted** — only allow the frontend origin.
- **Redis not publicly accessible** — only reachable via VPC connector from Cloud
  Run.
- **Short-lived tokens** — Epic tokens expire in minutes. Redis TTLs match.
- **PKCE** — prevents authorization code interception even without a client secret.

---

## Estimated Costs (GCP)

For 1–2 weeks of light usage:

| Service                | Monthly Rate    | Estimated Cost |
| ---------------------- | --------------- | -------------- |
| Cloud Run              | Pay-per-request | ~$1–5          |
| Memorystore Redis 1GB  | ~$7/month       | ~$3–7          |
| Cloud DNS              | $0.20/zone      | ~$0.20         |
| Artifact Registry      | $0.10/GB        | ~$0.10         |
| VPC Connector          | ~$7/month       | ~$3–7          |
| **Total**              |                 | **~$8–20**     |

---

## Glossary

| Term                  | Definition                                                                                   |
| --------------------- | -------------------------------------------------------------------------------------------- |
| FHIR                  | Fast Healthcare Interoperability Resources. HL7's standard for healthcare data exchange.      |
| SMART on FHIR         | Authorization framework layered on OAuth2, specifically for healthcare FHIR APIs.             |
| R4                    | FHIR Release 4 (version 4.0.1). The current stable release used by Epic.                     |
| PKCE                  | Proof Key for Code Exchange. OAuth2 extension that prevents auth code interception.           |
| Standalone Launch     | SMART flow where the app is opened directly by the user (vs. launched from within an EHR).    |
| EHR                   | Electronic Health Record system (e.g., Epic, Cerner).                                        |
| OperationOutcome      | FHIR resource returned by servers to communicate errors/warnings.                            |
| Bundle                | FHIR container resource that holds a collection of other resources (like a search result).    |
| Port (hexagonal)      | An interface defining how the domain communicates with the outside world.                     |
| Adapter (hexagonal)   | A concrete implementation of a port for a specific technology.                                |
| Driving adapter       | An adapter that *calls into* the domain (e.g., an HTTP controller).                          |
| Driven adapter        | An adapter that the domain *calls out to* (e.g., a database client).                         |
