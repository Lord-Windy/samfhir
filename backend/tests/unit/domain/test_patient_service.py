import json
from datetime import date

from tests.conftest import MockCachePort, MockFhirPort

from samfhir.domain.models.observation import CreateCondition, CreateObservation
from samfhir.domain.services.patient_service import PatientService


async def test_get_patient_returns_patient(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    patient = await service.get_patient("test-123")

    assert patient.id == "test-123"
    assert patient.family_name == "Test"
    assert patient.given_name == "Patient"
    assert patient.birth_date == date(1990, 1, 1)
    assert patient.gender == "male"


async def test_get_patient_summary_aggregates(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    summary = await service.get_patient_summary("test-123")

    assert summary.patient.family_name == "Test"
    assert len(summary.active_conditions) == 1
    assert summary.active_conditions[0].display == "Diabetes"
    assert len(summary.recent_observations) == 1
    assert len(summary.active_medications) == 1
    assert len(summary.allergies) == 1


async def test_cache_hit_skips_fhir(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)

    # First call — cache miss, populates cache
    await service.get_patient("test-123")
    assert mock_fhir_port.call_count["get_patient"] == 1

    # Second call — cache hit, FhirPort must NOT be called again
    await service.get_patient("test-123")
    assert mock_fhir_port.call_count["get_patient"] == 1


async def test_cache_miss_calls_fhir_then_stores(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)

    # Cache starts empty
    assert "patient:test-123" not in mock_cache_port._store

    await service.get_patient("test-123")

    # FhirPort was called
    assert mock_fhir_port.call_count["get_patient"] == 1

    # Result was stored in cache
    assert "patient:test-123" in mock_cache_port._store
    data = json.loads(mock_cache_port._store["patient:test-123"])
    assert data["family_name"] == "Test"


async def test_search_conditions_returns_conditions(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    conditions = await service.search_conditions("test-123")

    assert len(conditions) == 1
    assert conditions[0].display == "Diabetes"
    assert mock_fhir_port.call_count["search_conditions"] == 1

    # Second call — cache hit
    await service.search_conditions("test-123")
    assert mock_fhir_port.call_count["search_conditions"] == 1


async def test_search_observations_returns_observations(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    observations = await service.search_observations("test-123")

    assert len(observations) == 1
    assert observations[0].display == "BP Systolic"
    assert mock_fhir_port.call_count["search_observations"] == 1

    # Second call — cache hit
    await service.search_observations("test-123")
    assert mock_fhir_port.call_count["search_observations"] == 1


async def test_search_medications_returns_medications(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    medications = await service.search_medications("test-123")

    assert len(medications) == 1
    assert medications[0].display == "Metformin"
    assert mock_fhir_port.call_count["search_medications"] == 1

    # Second call — cache hit
    await service.search_medications("test-123")
    assert mock_fhir_port.call_count["search_medications"] == 1


async def test_search_allergies_returns_allergies(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    allergies = await service.search_allergies("test-123")

    assert len(allergies) == 1
    assert allergies[0].display == "Penicillin"
    assert mock_fhir_port.call_count["search_allergies"] == 1

    # Second call — cache hit
    await service.search_allergies("test-123")
    assert mock_fhir_port.call_count["search_allergies"] == 1


async def test_create_observation_delegates_and_invalidates_cache(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)

    # Prime the cache so we can verify invalidation
    await service.get_patient("test-123")
    assert "patient:test-123" in mock_cache_port._store

    obs = CreateObservation(
        patient_id="test-123",
        code="8480-6",
        display="BP Systolic",
        value="120",
        unit="mmHg",
        effective_date=date(2024, 6, 1),
    )
    result = await service.create_observation(obs)

    assert result.id == "new-obs-1"
    assert result.code == "8480-6"
    assert result.value == "120"
    assert mock_fhir_port.call_count["create_observation"] == 1

    # Cache should be invalidated
    assert "patient:test-123" not in mock_cache_port._store
    assert "patient_summary:test-123" not in mock_cache_port._store


async def test_create_condition_delegates_and_invalidates_cache(
    mock_fhir_port: MockFhirPort,
    mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)

    # Prime the cache so we can verify invalidation
    await service.search_conditions("test-123")
    assert "conditions:test-123" in mock_cache_port._store

    cond = CreateCondition(
        patient_id="test-123",
        code="44054006",
        display="Diabetes",
        clinical_status="active",
        onset_date=date(2020, 1, 1),
    )
    result = await service.create_condition(cond)

    assert result.id == "new-cond-1"
    assert result.code == "44054006"
    assert result.clinical_status == "active"
    assert mock_fhir_port.call_count["create_condition"] == 1

    # Cache should be invalidated
    assert "conditions:test-123" not in mock_cache_port._store
    assert "patient_summary:test-123" not in mock_cache_port._store
