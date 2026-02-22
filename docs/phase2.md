# Phase 2: HAPI FHIR Integration

## Goal

Replace the stub FHIR adapter with a live HAPI FHIR adapter. No authentication
required — HAPI's public R4 endpoint (`http://hapi.fhir.org/baseR4`) is open.
Demonstrate reading from and writing to a real FHIR server.

### What Changes from Phase 1

The hexagonal architecture means the domain layer (`models/`, `ports/`,
`services/`) stays almost untouched. The main work is:

1. A new outbound adapter (`hapi_fhir_client.py`) that implements `FhirPort`
2. New write methods on `FhirPort` and `PatientService`
3. New write endpoints and request schemas
4. Error handling for real FHIR server failures
5. Swapping `StubFhirClient` → `HapiFhirClient` in `main.py`

---

## Prerequisites

- Phase 1 complete and deployed
- No registration or credentials needed (HAPI is open)
- `fhirpy` and `fhir.resources` already in `pyproject.toml` (installed in Phase 1)

---

## Implementation Plan

### Step 1: HAPI FHIR Adapter — Read Operations

Implement the core adapter that replaces `StubFhirClient`.

**File to create:**

```
backend/src/samfhir/adapters/outbound/hapi_fhir_client.py
```

**What it does:**

- Implements `FhirPort` (all 6 existing abstract methods)
- Uses `fhirpy.AsyncFHIRClient` pointed at `http://hapi.fhir.org/baseR4`
- Maps FHIR R4 resources (`fhir.resources` Pydantic models) to our domain
  models (frozen dataclasses)

**Method-by-method mapping:**

| FhirPort Method         | FHIR Operation                           | Maps To              |
| ----------------------- | ---------------------------------------- | -------------------- |
| `get_patient(id)`       | `GET /Patient/{id}`                      | `Patient` dataclass  |
| `get_patient_summary(id)` | Calls all search methods + get_patient | `PatientSummary`     |
| `search_conditions(id)` | `GET /Condition?patient={id}`            | `list[Condition]`    |
| `search_observations(id)` | `GET /Observation?patient={id}`        | `list[Observation]`  |
| `search_medications(id)` | `GET /MedicationRequest?patient={id}`   | `list[Medication]`   |
| `search_allergies(id)`  | `GET /AllergyIntolerance?patient={id}`   | `list[Allergy]`      |

**FHIR → Domain mapping details:**

Each mapping function extracts fields from `fhir.resources` models into our
frozen dataclasses. Key mappings:

- `Patient.name[0].family` → `Patient.family_name`
- `Patient.name[0].given[0]` → `Patient.given_name`
- `Patient.birthDate` → `Patient.birth_date`
- `Condition.code.coding[0].code` → `Condition.code`
- `Condition.code.coding[0].display` → `Condition.display`
- `Condition.clinicalStatus.coding[0].code` → `Condition.clinical_status`
- `Observation.code.coding[0]` → code/display
- `Observation.valueQuantity.value` + `.unit` → value/unit
- `MedicationRequest.medicationCodeableConcept.coding[0]` → code/display
- `MedicationRequest.status` → `Medication.status`
- `AllergyIntolerance.code.coding[0]` → code/display
- `AllergyIntolerance.clinicalStatus.coding[0].code` → clinical_status
- `AllergyIntolerance.criticality` → criticality

Handle missing/optional fields gracefully (HAPI data is inconsistent).

**Constructor:**

```python
class HapiFhirClient(FhirPort):
    def __init__(self, base_url: str) -> None:
        self._client = AsyncFHIRClient(url=base_url)
```

### Step 2: Wire HAPI Adapter into Application

Swap the stub for the live adapter.

**Files to modify:**

- `backend/src/samfhir/main.py` — replace `StubFhirClient()` with
  `HapiFhirClient(settings.fhir_base_url)` in the lifespan function
- `backend/src/samfhir/config.py` — `fhir_base_url` already defaults to
  `http://hapi.fhir.org/baseR4`, no changes needed

**Change in `main.py`:**

```python
# Before (Phase 1):
app.state.fhir_client = StubFhirClient()

# After (Phase 2):
app.state.fhir_client = HapiFhirClient(settings.fhir_base_url)
```

The import changes from `stub_fhir_client` to `hapi_fhir_client`. Everything
else (dependency injection, routers, service layer) stays the same — that's
the point of hexagonal architecture.

### Step 3: FHIR Error Handling

FHIR servers return `OperationOutcome` resources on errors. Map these to
meaningful API responses instead of raw 500s.

**Files to create/modify:**

- `backend/src/samfhir/domain/models/errors.py` — domain error types
- `backend/src/samfhir/adapters/outbound/hapi_fhir_client.py` — catch and wrap
  FHIR errors
- `backend/src/samfhir/main.py` — register exception handlers

**Domain error types:**

```python
class PatientNotFoundError(Exception):
    def __init__(self, patient_id: str) -> None:
        self.patient_id = patient_id

class FhirServerError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
```

**Exception handlers in `main.py`:**

| Exception              | HTTP Status | Response Body                                    |
| ---------------------- | ----------- | ------------------------------------------------ |
| `PatientNotFoundError` | 404         | `{"error": "patient_not_found", "patient_id": ...}` |
| `FhirServerError`      | 502         | `{"error": "fhir_server_error", "detail": ...}`    |
| `ConnectionError`      | 503         | `{"error": "fhir_server_unavailable"}`              |

**In the adapter**, catch `fhirpy` exceptions and HAPI HTTP errors:

- 404 from HAPI → raise `PatientNotFoundError`
- 4xx/5xx from HAPI → raise `FhirServerError` with the OperationOutcome text
- Network failures → raise `FhirServerError` with connection context

Also update the `StubFhirClient` to raise `PatientNotFoundError` instead of
raw `ValueError` for consistency.

### Step 4: Write Operations — Domain Layer

Add write capability to the port, service, and domain models.

**Files to modify:**

- `backend/src/samfhir/domain/ports/fhir_port.py` — add write methods
- `backend/src/samfhir/domain/services/patient_service.py` — add write methods
- `backend/src/samfhir/domain/models/observation.py` — add input models

**New domain input models** (in `observation.py`):

```python
@dataclass(frozen=True)
class CreateObservation:
    """Input for creating an observation. No id — the server assigns it."""
    patient_id: str
    code: str
    display: str
    value: str
    unit: str | None
    effective_date: date | None

@dataclass(frozen=True)
class CreateCondition:
    """Input for creating a condition. No id — the server assigns it."""
    patient_id: str
    code: str
    display: str
    clinical_status: str
    onset_date: date | None
```

**New FhirPort methods:**

```python
@abstractmethod
async def create_observation(self, observation: "CreateObservation") -> "Observation": ...

@abstractmethod
async def create_condition(self, condition: "CreateCondition") -> "Condition": ...
```

**New PatientService methods:**

```python
async def create_observation(self, observation: CreateObservation) -> Observation:
    result = await self._fhir.create_observation(observation)
    await self.invalidate_patient_cache(observation.patient_id)
    return result

async def create_condition(self, condition: CreateCondition) -> Condition:
    result = await self._fhir.create_condition(condition)
    await self.invalidate_patient_cache(condition.patient_id)
    return result
```

Note: after writing, invalidate the patient cache so subsequent reads reflect
the new data.

### Step 5: Write Operations — HAPI Adapter

Implement the write methods in the HAPI adapter.

**File to modify:**

- `backend/src/samfhir/adapters/outbound/hapi_fhir_client.py`

**`create_observation` implementation:**

1. Build a `fhir.resources.observation.Observation` with:
   - `status = "final"`
   - `code.coding[0]` from the input code/display
   - `subject.reference = f"Patient/{patient_id}"`
   - `valueQuantity` from input value/unit
   - `effectiveDateTime` from input effective_date
2. POST to `/Observation` via fhirpy
3. Map the server response (with assigned ID) back to our `Observation` domain
   model

**`create_condition` implementation:**

1. Build a `fhir.resources.condition.Condition` with:
   - `clinicalStatus.coding[0].code` from input
   - `code.coding[0]` from input code/display
   - `subject.reference = f"Patient/{patient_id}"`
   - `onsetDateTime` from input onset_date
2. POST to `/Condition` via fhirpy
3. Map the server response back to our `Condition` domain model

Also update `StubFhirClient` to implement the new write methods (append to
in-memory lists and return with generated IDs).

### Step 6: Write Endpoints — API Layer

Add POST endpoints for creating observations and conditions.

**Files to modify:**

- `backend/src/samfhir/adapters/inbound/api/schemas/patient_schemas.py` — add
  request schemas
- `backend/src/samfhir/adapters/inbound/api/patient_router.py` — add POST
  endpoints

**New request schemas:**

```python
class CreateObservationRequest(BaseModel):
    patient_id: str
    code: str
    display: str
    value: str
    unit: str | None = None
    effective_date: date | None = None

class CreateConditionRequest(BaseModel):
    patient_id: str
    code: str
    display: str
    clinical_status: str = "active"
    onset_date: date | None = None
```

**New endpoints:**

| Method | Path                      | Request Body              | Response             |
| ------ | ------------------------- | ------------------------- | -------------------- |
| POST   | `/api/v1/observations`    | `CreateObservationRequest` | `ObservationResponse` (201) |
| POST   | `/api/v1/conditions`      | `CreateConditionRequest`   | `ConditionResponse` (201)  |

These live on the existing `patient_router` (or a new `write_router` — either
works, but keeping them on `patient_router` is simpler since they share the
same service dependency).

### Step 7: Seed Data Script

HAPI data is periodically purged. Provide a way to create test data.

**File to create:**

```
backend/src/samfhir/seed.py
```

**What it does:**

- Creates a test patient (Jason Argonaut-style) in HAPI via `POST /Patient`
- Creates a set of conditions, observations, medications, and allergies linked
  to that patient
- Prints the created patient ID for use in testing
- Can be run as: `uv run python -m samfhir.seed`

Also consider adding a `POST /api/v1/seed` endpoint (behind a debug flag) that
creates test data and returns the patient ID. Useful for demos.

### Step 8: Patient Search Endpoint

Currently all endpoints require a known patient ID. Add a search endpoint so
users can find patients by name.

**Files to modify:**

- `backend/src/samfhir/domain/ports/fhir_port.py` — add `search_patients`
- `backend/src/samfhir/domain/services/patient_service.py` — add
  `search_patients`
- `backend/src/samfhir/adapters/outbound/hapi_fhir_client.py` — implement
  search
- `backend/src/samfhir/adapters/outbound/stub_fhir_client.py` — implement
  search
- `backend/src/samfhir/adapters/inbound/api/patient_router.py` — add GET
  endpoint

**New FhirPort method:**

```python
@abstractmethod
async def search_patients(self, name: str | None = None) -> list["Patient"]: ...
```

**New endpoint:**

| Method | Path                | Query Params   | Response                |
| ------ | ------------------- | -------------- | ----------------------- |
| GET    | `/api/v1/patients`  | `?name=...`    | `list[PatientResponse]` |

The HAPI adapter uses `GET /Patient?name={name}` to search.

### Step 9: Tests

**Files to create/modify:**

```
backend/tests/unit/domain/test_patient_service.py    # modify — add write tests
backend/tests/integration/test_patient_router.py     # modify — add write + error tests
backend/tests/unit/adapters/test_hapi_fhir_client.py # new — unit tests for mapping logic
backend/tests/integration/test_hapi_live.py          # new — live integration tests (optional)
```

**Unit tests for HAPI adapter (`test_hapi_fhir_client.py`):**

- Test FHIR → domain model mapping with sample FHIR JSON
- Test handling of missing/optional fields (no `valueQuantity`, no `name`, etc.)
- Test error mapping (404 → `PatientNotFoundError`, 500 → `FhirServerError`)

**Unit tests for write operations (`test_patient_service.py`):**

- `create_observation` calls `FhirPort.create_observation` and invalidates
  cache
- `create_condition` calls `FhirPort.create_condition` and invalidates cache

**Integration tests for write endpoints (`test_patient_router.py`):**

- POST `/api/v1/observations` returns 201 with the created resource
- POST `/api/v1/conditions` returns 201 with the created resource
- POST with missing required fields returns 422

**Integration tests for error handling:**

- GET patient with non-existent ID returns 404 with structured error
- Structured error response matches expected schema

**Live integration tests (`test_hapi_live.py`):**

- Marked with `@pytest.mark.live` — skipped by default, run manually
- Create a patient, read it back, create an observation, verify summary
- Tests the full round-trip against the real HAPI server

Update `conftest.py` mock ports to implement the new write methods.

---

## Acceptance Criteria

- [ ] `GET /api/v1/patients/{id}` returns real patient data from HAPI FHIR
- [ ] `GET /api/v1/patients/{id}/summary` aggregates real data from multiple
      FHIR resources
- [ ] `GET /api/v1/patients?name=...` searches for patients by name
- [ ] `POST /api/v1/observations` successfully creates an observation in HAPI
- [ ] `POST /api/v1/conditions` successfully creates a condition in HAPI
- [ ] Cache stats show hits on repeated requests for the same patient
- [ ] OperationOutcome errors are returned as structured JSON error responses
- [ ] Non-existent patient IDs return 404 (not 500)
- [ ] HAPI downtime results in 503 (not unhandled exception)
- [ ] `make test` passes (all existing + new tests)
- [ ] `make lint` passes with zero warnings

---

## Key Decisions

| Decision              | Choice                        | Rationale                                                      |
| --------------------- | ----------------------------- | -------------------------------------------------------------- |
| FHIR client library   | `fhirpy` (async)              | Async, clean API, no opinion on auth (we handle that).         |
| FHIR models           | `fhir.resources`              | Pydantic v2 models for validation/serialization of FHIR JSON.  |
| FHIR server           | HAPI FHIR (open)              | No registration, no auth. Immediate live data.                 |
| FHIR version          | R4                            | Standard version supported by HAPI, Epic, and Cerner.          |
| Write-back resources  | Observation + Condition       | Shows bidirectional capability without needing auth scopes.    |
| Error model           | Domain exceptions + handlers  | Keeps error logic in domain, maps to HTTP in the adapter layer. |
| Seed data             | Script + optional endpoint    | HAPI purges periodically; easy recreation for demos.           |

---

## Implementation Order

```
Step 1: HAPI FHIR adapter (read operations)
  │
  ▼
Step 2: Wire adapter into main.py (swap stub → HAPI)
  │
  ▼
Step 3: Error handling (domain errors + exception handlers)
  │
  ├─── can now test read operations end-to-end against HAPI
  │
  ▼
Step 4: Write operations — domain layer (port + service + input models)
  │
  ▼
Step 5: Write operations — HAPI adapter implementation
  │
  ▼
Step 6: Write endpoints — API layer (POST routes + request schemas)
  │
  ├─── can now test write operations end-to-end against HAPI
  │
  ▼
Step 7: Seed data script
  │
  ▼
Step 8: Patient search endpoint
  │
  ▼
Step 9: Tests (unit + integration + live)
  │
  ▼
Deploy + verify acceptance criteria
```

**Parallelizable work:**

- Steps 7 and 8 are independent of each other (can be done in parallel)
- Step 9 tests should be written alongside each step, but the live integration
  tests require steps 1–6 to be complete

---

## Files Summary

**New files:**

| File | Purpose |
| ---- | ------- |
| `backend/src/samfhir/adapters/outbound/hapi_fhir_client.py` | HAPI FHIR adapter implementing FhirPort |
| `backend/src/samfhir/domain/models/errors.py` | Domain error types |
| `backend/src/samfhir/seed.py` | Seed data script for HAPI |
| `backend/tests/unit/adapters/test_hapi_fhir_client.py` | Unit tests for FHIR mapping |
| `backend/tests/integration/test_hapi_live.py` | Live integration tests |

**Modified files:**

| File | Change |
| ---- | ------ |
| `backend/src/samfhir/main.py` | Swap stub → HAPI adapter, add exception handlers |
| `backend/src/samfhir/domain/ports/fhir_port.py` | Add `create_observation`, `create_condition`, `search_patients` |
| `backend/src/samfhir/domain/services/patient_service.py` | Add write + search methods |
| `backend/src/samfhir/domain/models/observation.py` | Add `CreateObservation`, `CreateCondition` input models |
| `backend/src/samfhir/adapters/outbound/stub_fhir_client.py` | Implement new port methods, use domain errors |
| `backend/src/samfhir/adapters/inbound/api/patient_router.py` | Add POST + search endpoints |
| `backend/src/samfhir/adapters/inbound/api/schemas/patient_schemas.py` | Add request schemas |
| `backend/tests/conftest.py` | Update mock ports with new methods |
| `backend/tests/unit/domain/test_patient_service.py` | Add write operation tests |
| `backend/tests/integration/test_patient_router.py` | Add write + error tests |
