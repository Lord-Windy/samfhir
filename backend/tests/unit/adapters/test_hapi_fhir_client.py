"""Unit tests for HapiFhirClient FHIR-to-domain mapping functions."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from fhirpy.base.exceptions import OperationOutcome, ResourceNotFound

from samfhir.domain.models.errors import FhirServerError, PatientNotFoundError
from samfhir.domain.models.observation import CreateCondition, CreateObservation

from samfhir.adapters.outbound.hapi_fhir_client import (
    HapiFhirClient,
    _extract_status_code,
    _map_allergy,
    _map_condition,
    _map_medication,
    _map_observation,
    _map_patient,
    _safe_coding,
    _safe_date,
)


# ── _safe_coding ──


def test_safe_coding_with_valid_codeable_concept():
    cc = {"coding": [{"code": "123", "display": "Test"}]}
    assert _safe_coding(cc) == ("123", "Test")


def test_safe_coding_none():
    assert _safe_coding(None) == ("unknown", "unknown")


def test_safe_coding_empty_coding_list():
    assert _safe_coding({"coding": []}) == ("unknown", "unknown")


def test_safe_coding_falls_back_to_text():
    assert _safe_coding({"coding": [], "text": "Free text"}) == ("unknown", "Free text")


def test_safe_coding_missing_display():
    cc = {"coding": [{"code": "123"}]}
    assert _safe_coding(cc) == ("123", "unknown")


# ── _safe_date ──


def test_safe_date_valid_date():
    assert _safe_date("2024-03-15") == date(2024, 3, 15)


def test_safe_date_datetime_string():
    assert _safe_date("2024-03-15T10:30:00Z") == date(2024, 3, 15)


def test_safe_date_none():
    assert _safe_date(None) is None


def test_safe_date_invalid():
    assert _safe_date("not-a-date") is None


# ── _map_patient ──


def test_map_patient_full_data():
    data = {
        "id": "123",
        "name": [{"family": "Doe", "given": ["John"]}],
        "birthDate": "1990-05-20",
        "gender": "male",
    }
    p = _map_patient(data)
    assert p.id == "123"
    assert p.family_name == "Doe"
    assert p.given_name == "John"
    assert p.birth_date == date(1990, 5, 20)
    assert p.gender == "male"


def test_map_patient_missing_name():
    data = {"id": "123", "gender": "female"}
    p = _map_patient(data)
    assert p.family_name == "Unknown"
    assert p.given_name == "Unknown"


def test_map_patient_empty_given():
    data = {"id": "123", "name": [{"family": "Smith", "given": []}]}
    p = _map_patient(data)
    assert p.given_name == "Unknown"


def test_map_patient_missing_birth_date():
    data = {"id": "123", "name": [{"family": "X", "given": ["Y"]}]}
    p = _map_patient(data)
    assert p.birth_date == date(1900, 1, 1)


# ── _map_condition ──


def test_map_condition_full_data():
    data = {
        "id": "cond-1",
        "code": {"coding": [{"code": "44054006", "display": "Diabetes"}]},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2020-01-15",
    }
    c = _map_condition(data)
    assert c.id == "cond-1"
    assert c.code == "44054006"
    assert c.display == "Diabetes"
    assert c.clinical_status == "active"
    assert c.onset_date == date(2020, 1, 15)


def test_map_condition_missing_optional_fields():
    data = {"id": "cond-2", "code": None, "clinicalStatus": None}
    c = _map_condition(data)
    assert c.code == "unknown"
    assert c.clinical_status == "unknown"
    assert c.onset_date is None


# ── _map_observation ──


def test_map_observation_with_quantity():
    data = {
        "id": "obs-1",
        "code": {"coding": [{"code": "8480-6", "display": "Systolic BP"}]},
        "valueQuantity": {"value": 120, "unit": "mmHg"},
        "effectiveDateTime": "2024-02-15",
    }
    o = _map_observation(data)
    assert o.code == "8480-6"
    assert o.value == "120"
    assert o.unit == "mmHg"
    assert o.effective_date == date(2024, 2, 15)


def test_map_observation_with_value_string():
    data = {
        "id": "obs-2",
        "code": {"coding": [{"code": "X", "display": "Y"}]},
        "valueString": "Positive",
    }
    o = _map_observation(data)
    assert o.value == "Positive"
    assert o.unit is None


def test_map_observation_no_value():
    data = {"id": "obs-3", "code": {"coding": [{"code": "X", "display": "Y"}]}}
    o = _map_observation(data)
    assert o.value == ""
    assert o.unit is None


# ── _map_medication ──


def test_map_medication_full_data():
    data = {
        "id": "med-1",
        "medicationCodeableConcept": {
            "coding": [{"code": "861007", "display": "Metformin 500mg"}]
        },
        "status": "active",
        "authoredOn": "2023-06-01",
    }
    m = _map_medication(data)
    assert m.code == "861007"
    assert m.display == "Metformin 500mg"
    assert m.status == "active"
    assert m.authored_on == date(2023, 6, 1)


def test_map_medication_missing_concept():
    data = {"id": "med-2", "status": "stopped"}
    m = _map_medication(data)
    assert m.code == "unknown"
    assert m.display == "unknown"


# ── _map_allergy ──


def test_map_allergy_full_data():
    data = {
        "id": "allergy-1",
        "code": {"coding": [{"code": "763875007", "display": "Penicillin"}]},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "criticality": "high",
    }
    a = _map_allergy(data)
    assert a.code == "763875007"
    assert a.display == "Penicillin"
    assert a.clinical_status == "active"
    assert a.criticality == "high"


def test_map_allergy_missing_criticality():
    data = {
        "id": "allergy-2",
        "code": {"coding": [{"code": "X", "display": "Y"}]},
        "clinicalStatus": {"coding": [{"code": "active"}]},
    }
    a = _map_allergy(data)
    assert a.criticality is None


# ── _extract_status_code ──


def test_extract_status_code_invalid_issue_type():
    from fhirpy.base.exceptions import OperationOutcome

    exc = OperationOutcome(reason="Bad input", code="invalid")
    assert _extract_status_code(exc) == 400


def test_extract_status_code_exception_issue_type():
    from fhirpy.base.exceptions import OperationOutcome

    exc = OperationOutcome(reason="Server crash", code="exception")
    assert _extract_status_code(exc) == 500


def test_extract_status_code_from_resource_dict():
    from fhirpy.base.exceptions import OperationOutcome

    exc = OperationOutcome(
        resource={
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "error", "code": "throttled", "diagnostics": "Rate limited"}],
        }
    )
    assert _extract_status_code(exc) == 429


def test_extract_status_code_unknown_code_defaults_to_500():
    from fhirpy.base.exceptions import OperationOutcome

    exc = OperationOutcome(
        resource={
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "error", "code": "unknown-code"}],
        }
    )
    assert _extract_status_code(exc) == 500


def test_extract_status_code_no_resource_defaults_to_500():
    from fhirpy.base.exceptions import OperationOutcome

    exc = OperationOutcome.__new__(OperationOutcome)
    # No resource attribute at all
    assert _extract_status_code(exc) == 500


# ── HapiFhirClient integration (mocked fhirpy) ──


@pytest.fixture
def client():
    with patch("samfhir.adapters.outbound.hapi_fhir_client.AsyncFHIRClient"):
        return HapiFhirClient("http://test.example.com/fhir")


async def test_get_patient_calls_fhirpy(client):
    mock_resource = {
        "id": "test-123",
        "name": [{"family": "Test", "given": ["User"]}],
        "birthDate": "2000-01-01",
        "gender": "female",
    }
    mock_ref = AsyncMock()
    mock_ref.to_resource.return_value = mock_resource
    client._client.reference = lambda *a, **kw: mock_ref

    patient = await client.get_patient("test-123")
    assert patient.id == "test-123"
    assert patient.family_name == "Test"
    assert patient.given_name == "User"


async def test_get_patient_not_found_raises_patient_not_found_error(client):
    mock_ref = AsyncMock()
    mock_ref.to_resource.side_effect = ResourceNotFound()
    client._client.reference = lambda *a, **kw: mock_ref

    with pytest.raises(PatientNotFoundError) as exc_info:
        await client.get_patient("nonexistent")
    assert exc_info.value.patient_id == "nonexistent"


async def test_get_patient_operation_outcome_raises_fhir_server_error(client):
    mock_ref = AsyncMock()
    mock_ref.to_resource.side_effect = OperationOutcome(reason="Server error")
    client._client.reference = lambda *a, **kw: mock_ref

    with pytest.raises(FhirServerError) as exc_info:
        await client.get_patient("test-123")
    # Default issue type is "invalid" → 400
    assert exc_info.value.status_code == 400


async def test_get_patient_operation_outcome_propagates_exception_status(client):
    from fhirpy.base.exceptions import OperationOutcome

    from samfhir.domain.models.errors import FhirServerError

    mock_ref = AsyncMock()
    mock_ref.to_resource.side_effect = OperationOutcome(
        resource={
            "resourceType": "OperationOutcome",
            "issue": [
                {"severity": "error", "code": "exception", "diagnostics": "Internal"}
            ],
        }
    )
    client._client.reference = lambda *a, **kw: mock_ref

    with pytest.raises(FhirServerError) as exc_info:
        await client.get_patient("test-123")
    assert exc_info.value.status_code == 500


async def test_get_patient_connection_error(client):
    mock_ref = AsyncMock()
    mock_ref.to_resource.side_effect = aiohttp.ClientConnectionError(
        "Connection refused"
    )
    client._client.reference = lambda *a, **kw: mock_ref

    with pytest.raises(ConnectionError):
        await client.get_patient("test-123")


async def test_search_not_found_raises_patient_not_found_error(client):
    mock_searchset = MagicMock()
    mock_searchset.search.return_value = mock_searchset
    mock_searchset.limit.return_value = mock_searchset
    mock_searchset.fetch = AsyncMock(side_effect=ResourceNotFound())
    client._client.resources = lambda rt: mock_searchset

    with pytest.raises(PatientNotFoundError):
        await client.search_conditions("nonexistent")


async def test_search_operation_outcome_raises_fhir_server_error(client):
    mock_searchset = MagicMock()
    mock_searchset.search.return_value = mock_searchset
    mock_searchset.limit.return_value = mock_searchset
    mock_searchset.fetch = AsyncMock(
        side_effect=OperationOutcome(reason="Internal server error")
    )
    client._client.resources = lambda rt: mock_searchset

    with pytest.raises(FhirServerError) as exc_info:
        await client.search_conditions("test-123")
    # Default issue type is "invalid" → 400
    assert exc_info.value.status_code == 400


async def test_search_conditions(client):
    mock_searchset = MagicMock()
    mock_searchset.search.return_value = mock_searchset
    mock_searchset.limit.return_value = mock_searchset
    mock_searchset.fetch = AsyncMock(
        return_value=[
            {
                "id": "cond-1",
                "code": {"coding": [{"code": "123", "display": "Flu"}]},
                "clinicalStatus": {"coding": [{"code": "resolved"}]},
                "onsetDateTime": "2024-01-01",
            }
        ]
    )
    client._client.resources = lambda rt: mock_searchset

    conditions = await client.search_conditions("patient-1")
    assert len(conditions) == 1
    assert conditions[0].code == "123"
    assert conditions[0].clinical_status == "resolved"


async def test_get_patient_summary_filters_active(client):
    mock_ref = AsyncMock()
    mock_ref.to_resource.return_value = {
        "id": "p1",
        "name": [{"family": "A", "given": ["B"]}],
        "birthDate": "1990-01-01",
        "gender": "male",
    }
    client._client.reference = lambda *a, **kw: mock_ref

    mock_searchset = MagicMock()
    mock_searchset.search.return_value = mock_searchset
    mock_searchset.limit.return_value = mock_searchset

    call_count = 0
    fetch_results = [
        # conditions
        [
            {
                "id": "c1",
                "code": {"coding": [{"code": "1", "display": "A"}]},
                "clinicalStatus": {"coding": [{"code": "active"}]},
            },
            {
                "id": "c2",
                "code": {"coding": [{"code": "2", "display": "B"}]},
                "clinicalStatus": {"coding": [{"code": "resolved"}]},
            },
        ],
        # observations
        [],
        # medications
        [
            {
                "id": "m1",
                "medicationCodeableConcept": {
                    "coding": [{"code": "3", "display": "C"}]
                },
                "status": "active",
            },
            {
                "id": "m2",
                "medicationCodeableConcept": {
                    "coding": [{"code": "4", "display": "D"}]
                },
                "status": "stopped",
            },
        ],
        # allergies
        [],
    ]

    async def mock_fetch():
        nonlocal call_count
        result = fetch_results[call_count]
        call_count += 1
        return result

    mock_searchset.fetch = mock_fetch
    client._client.resources = lambda rt: mock_searchset

    summary = await client.get_patient_summary("p1")
    assert len(summary.active_conditions) == 1
    assert summary.active_conditions[0].id == "c1"
    assert len(summary.active_medications) == 1
    assert summary.active_medications[0].id == "m1"


# ── create_observation ──


async def test_create_observation_success(client):
    observation_input = CreateObservation(
        patient_id="patient-1",
        code="8480-6",
        display="Systolic Blood Pressure",
        value="120",
        unit="mmHg",
        effective_date=date(2024, 2, 15),
    )

    saved_resource = {
        "id": "obs-new",
        "code": {"coding": [{"code": "8480-6", "display": "Systolic Blood Pressure"}]},
        "valueQuantity": {"value": 120, "unit": "mmHg"},
        "effectiveDateTime": "2024-02-15",
    }

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(return_value=saved_resource)
    client._client.resource = lambda rt, **kw: mock_resource

    result = await client.create_observation(observation_input)

    assert result.id == "obs-new"
    assert result.code == "8480-6"
    assert result.display == "Systolic Blood Pressure"
    assert result.value == "120"
    assert result.unit == "mmHg"
    assert result.effective_date == date(2024, 2, 15)


async def test_create_observation_builds_correct_fhir_resource(client):
    observation_input = CreateObservation(
        patient_id="patient-1",
        code="8480-6",
        display="Systolic Blood Pressure",
        value="120",
        unit="mmHg",
        effective_date=date(2024, 2, 15),
    )

    captured_kwargs = {}

    def capture_resource(rt, **kwargs):
        captured_kwargs["resource_type"] = rt
        captured_kwargs["data"] = kwargs
        mock_resource = AsyncMock()
        mock_resource.save = AsyncMock(
            return_value={
                "id": "obs-1",
                "code": {
                    "coding": [{"code": "8480-6", "display": "Systolic Blood Pressure"}]
                },
                "valueQuantity": {"value": 120, "unit": "mmHg"},
                "effectiveDateTime": "2024-02-15",
            }
        )
        return mock_resource

    client._client.resource = capture_resource

    await client.create_observation(observation_input)

    assert captured_kwargs["resource_type"] == "Observation"
    data = captured_kwargs["data"]
    assert data["resourceType"] == "Observation"
    assert data["status"] == "final"
    assert data["code"]["coding"][0]["code"] == "8480-6"
    assert data["code"]["coding"][0]["display"] == "Systolic Blood Pressure"
    assert data["subject"]["reference"] == "Patient/patient-1"
    assert data["valueQuantity"]["value"] == 120.0
    assert data["valueQuantity"]["unit"] == "mmHg"
    assert data["effectiveDateTime"] == "2024-02-15"


async def test_create_observation_without_effective_date(client):
    observation_input = CreateObservation(
        patient_id="patient-1",
        code="8480-6",
        display="Systolic Blood Pressure",
        value="120",
        unit="mmHg",
        effective_date=None,
    )

    captured_kwargs = {}

    def capture_resource(rt, **kwargs):
        captured_kwargs["data"] = kwargs
        mock_resource = AsyncMock()
        mock_resource.save = AsyncMock(
            return_value={
                "id": "obs-1",
                "code": {
                    "coding": [{"code": "8480-6", "display": "Systolic Blood Pressure"}]
                },
                "valueQuantity": {"value": 120, "unit": "mmHg"},
            }
        )
        return mock_resource

    client._client.resource = capture_resource

    await client.create_observation(observation_input)

    assert "effectiveDateTime" not in captured_kwargs["data"]


async def test_create_observation_resource_not_found_raises_patient_not_found_error(
    client,
):
    observation_input = CreateObservation(
        patient_id="nonexistent",
        code="8480-6",
        display="Test",
        value="120",
        unit="mmHg",
        effective_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(side_effect=ResourceNotFound())
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(PatientNotFoundError) as exc_info:
        await client.create_observation(observation_input)
    assert exc_info.value.patient_id == "nonexistent"
    mock_resource.save.assert_awaited_once()


async def test_create_observation_operation_outcome_raises_fhir_server_error(client):
    observation_input = CreateObservation(
        patient_id="patient-1",
        code="8480-6",
        display="Test",
        value="120",
        unit="mmHg",
        effective_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(side_effect=OperationOutcome(reason="Server error"))
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(FhirServerError):
        await client.create_observation(observation_input)
    mock_resource.save.assert_awaited_once()


async def test_create_observation_connection_error(client):
    observation_input = CreateObservation(
        patient_id="patient-1",
        code="8480-6",
        display="Test",
        value="120",
        unit="mmHg",
        effective_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(
        side_effect=aiohttp.ClientConnectionError("Connection refused")
    )
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(ConnectionError):
        await client.create_observation(observation_input)
    mock_resource.save.assert_awaited_once()


# ── create_condition ──


async def test_create_condition_success(client):
    condition_input = CreateCondition(
        patient_id="patient-1",
        code="44054006",
        display="Diabetes mellitus",
        clinical_status="active",
        onset_date=date(2020, 1, 15),
    )

    saved_resource = {
        "id": "cond-new",
        "code": {"coding": [{"code": "44054006", "display": "Diabetes mellitus"}]},
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "onsetDateTime": "2020-01-15",
    }

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(return_value=saved_resource)
    client._client.resource = lambda rt, **kw: mock_resource

    result = await client.create_condition(condition_input)

    assert result.id == "cond-new"
    assert result.code == "44054006"
    assert result.display == "Diabetes mellitus"
    assert result.clinical_status == "active"
    assert result.onset_date == date(2020, 1, 15)


async def test_create_condition_builds_correct_fhir_resource(client):
    condition_input = CreateCondition(
        patient_id="patient-1",
        code="44054006",
        display="Diabetes mellitus",
        clinical_status="active",
        onset_date=date(2020, 1, 15),
    )

    captured_kwargs = {}

    def capture_resource(rt, **kwargs):
        captured_kwargs["resource_type"] = rt
        captured_kwargs["data"] = kwargs
        mock_resource = AsyncMock()
        mock_resource.save = AsyncMock(
            return_value={
                "id": "cond-1",
                "code": {
                    "coding": [{"code": "44054006", "display": "Diabetes mellitus"}]
                },
                "clinicalStatus": {"coding": [{"code": "active"}]},
                "onsetDateTime": "2020-01-15",
            }
        )
        return mock_resource

    client._client.resource = capture_resource

    await client.create_condition(condition_input)

    assert captured_kwargs["resource_type"] == "Condition"
    data = captured_kwargs["data"]
    assert data["resourceType"] == "Condition"
    assert data["clinicalStatus"]["coding"][0]["code"] == "active"
    assert data["code"]["coding"][0]["code"] == "44054006"
    assert data["code"]["coding"][0]["display"] == "Diabetes mellitus"
    assert data["subject"]["reference"] == "Patient/patient-1"
    assert data["onsetDateTime"] == "2020-01-15"


async def test_create_condition_without_onset_date(client):
    condition_input = CreateCondition(
        patient_id="patient-1",
        code="44054006",
        display="Diabetes mellitus",
        clinical_status="active",
        onset_date=None,
    )

    captured_kwargs = {}

    def capture_resource(rt, **kwargs):
        captured_kwargs["data"] = kwargs
        mock_resource = AsyncMock()
        mock_resource.save = AsyncMock(
            return_value={
                "id": "cond-1",
                "code": {
                    "coding": [{"code": "44054006", "display": "Diabetes mellitus"}]
                },
                "clinicalStatus": {"coding": [{"code": "active"}]},
            }
        )
        return mock_resource

    client._client.resource = capture_resource

    await client.create_condition(condition_input)

    assert "onsetDateTime" not in captured_kwargs["data"]


async def test_create_condition_resource_not_found_raises_patient_not_found_error(
    client,
):
    condition_input = CreateCondition(
        patient_id="nonexistent",
        code="44054006",
        display="Test",
        clinical_status="active",
        onset_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(side_effect=ResourceNotFound())
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(PatientNotFoundError) as exc_info:
        await client.create_condition(condition_input)
    assert exc_info.value.patient_id == "nonexistent"
    mock_resource.save.assert_awaited_once()


async def test_create_condition_operation_outcome_raises_fhir_server_error(client):
    condition_input = CreateCondition(
        patient_id="patient-1",
        code="44054006",
        display="Test",
        clinical_status="active",
        onset_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(side_effect=OperationOutcome(reason="Server error"))
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(FhirServerError):
        await client.create_condition(condition_input)
    mock_resource.save.assert_awaited_once()


async def test_create_condition_connection_error(client):
    condition_input = CreateCondition(
        patient_id="patient-1",
        code="44054006",
        display="Test",
        clinical_status="active",
        onset_date=None,
    )

    mock_resource = AsyncMock()
    mock_resource.save = AsyncMock(
        side_effect=aiohttp.ClientConnectionError("Connection refused")
    )
    client._client.resource = lambda rt, **kw: mock_resource

    with pytest.raises(ConnectionError):
        await client.create_condition(condition_input)
    mock_resource.save.assert_awaited_once()
