import json
from datetime import date

from tests.conftest import MockCachePort, MockFhirPort

from samfhir.domain.services.patient_service import PatientService


async def test_get_patient_returns_patient(
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    patient = await service.get_patient("test-123")

    assert patient.id == "test-123"
    assert patient.family_name == "Test"
    assert patient.given_name == "Patient"
    assert patient.birth_date == date(1990, 1, 1)
    assert patient.gender == "male"


async def test_get_patient_summary_aggregates(
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
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
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)

    # First call — cache miss, populates cache
    await service.get_patient("test-123")
    assert mock_fhir_port.call_count["get_patient"] == 1

    # Second call — cache hit, FhirPort must NOT be called again
    await service.get_patient("test-123")
    assert mock_fhir_port.call_count["get_patient"] == 1


async def test_cache_miss_calls_fhir_then_stores(
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
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
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
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
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
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
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
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
    mock_fhir_port: MockFhirPort, mock_cache_port: MockCachePort,
):
    service = PatientService(mock_fhir_port, mock_cache_port)
    allergies = await service.search_allergies("test-123")

    assert len(allergies) == 1
    assert allergies[0].display == "Penicillin"
    assert mock_fhir_port.call_count["search_allergies"] == 1

    # Second call — cache hit
    await service.search_allergies("test-123")
    assert mock_fhir_port.call_count["search_allergies"] == 1
