"""Live integration tests against the public HAPI FHIR R4 server.

Run with: cd backend && uv run pytest -m live -v
Skipped by default in normal pytest runs.
"""

import uuid
from datetime import date

import httpx
import pytest

from samfhir.adapters.outbound.hapi_fhir_client import HapiFhirClient
from samfhir.domain.models.errors import PatientNotFoundError
from samfhir.domain.models.observation import CreateCondition, CreateObservation

HAPI_BASE_URL = "http://hapi.fhir.org/baseR4"

pytestmark = pytest.mark.live


@pytest.fixture
def hapi_client():
    return HapiFhirClient(HAPI_BASE_URL)


async def _create_test_patient() -> str:
    """Create a Patient on HAPI and return its server-assigned ID."""
    unique = uuid.uuid4().hex[:8]
    patient_resource = {
        "resourceType": "Patient",
        "name": [{"family": f"TestLive-{unique}", "given": ["SamFHIR"]}],
        "birthDate": "1990-01-01",
        "gender": "female",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{HAPI_BASE_URL}/Patient",
            json=patient_resource,
            headers={"Content-Type": "application/fhir+json"},
        )
        resp.raise_for_status()
        return resp.json()["id"]


async def test_create_and_read_patient(hapi_client: HapiFhirClient):
    patient_id = await _create_test_patient()
    patient = await hapi_client.get_patient(patient_id)

    assert patient.id == patient_id
    assert patient.given_name == "SamFHIR"
    assert patient.birth_date == date(1990, 1, 1)
    assert patient.gender == "female"


async def test_create_observation_and_verify(hapi_client: HapiFhirClient):
    patient_id = await _create_test_patient()
    obs_input = CreateObservation(
        patient_id=patient_id,
        code="8867-4",
        display="Heart rate",
        value="72",
        unit="bpm",
        effective_date=date(2024, 6, 1),
    )
    result = await hapi_client.create_observation(obs_input)

    assert result.id
    assert result.code == "8867-4"
    assert result.display == "Heart rate"
    assert result.value == "72.0"
    assert result.unit == "bpm"
    assert result.effective_date == date(2024, 6, 1)


async def test_create_condition_and_verify(hapi_client: HapiFhirClient):
    patient_id = await _create_test_patient()
    cond_input = CreateCondition(
        patient_id=patient_id,
        code="73211009",
        display="Diabetes mellitus",
        clinical_status="active",
        onset_date=date(2023, 3, 15),
    )
    result = await hapi_client.create_condition(cond_input)

    assert result.id
    assert result.code == "73211009"
    assert result.display == "Diabetes mellitus"
    assert result.clinical_status == "active"
    assert result.onset_date == date(2023, 3, 15)


async def test_full_round_trip(hapi_client: HapiFhirClient):
    patient_id = await _create_test_patient()

    await hapi_client.create_observation(
        CreateObservation(
            patient_id=patient_id,
            code="8480-6",
            display="Systolic blood pressure",
            value="120",
            unit="mmHg",
            effective_date=date(2024, 6, 1),
        )
    )
    await hapi_client.create_condition(
        CreateCondition(
            patient_id=patient_id,
            code="38341003",
            display="Hypertension",
            clinical_status="active",
            onset_date=date(2023, 1, 1),
        )
    )

    summary = await hapi_client.get_patient_summary(patient_id)
    assert summary.patient.id == patient_id
    assert len(summary.recent_observations) >= 1
    assert any(o.code == "8480-6" for o in summary.recent_observations)
    assert len(summary.active_conditions) >= 1
    assert any(c.code == "38341003" for c in summary.active_conditions)


async def test_get_nonexistent_patient_raises_not_found(
    hapi_client: HapiFhirClient,
):
    with pytest.raises(PatientNotFoundError):
        await hapi_client.get_patient("nonexistent-uuid-99999")
