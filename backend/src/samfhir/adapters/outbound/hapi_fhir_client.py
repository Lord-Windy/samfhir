import asyncio
from datetime import date

import aiohttp
from fhirpy import AsyncFHIRClient
from fhirpy.base.exceptions import OperationOutcome, ResourceNotFound

from samfhir.domain.models.errors import FhirServerError, PatientNotFoundError
from samfhir.domain.models.observation import (
    Allergy,
    Condition,
    CreateCondition,
    CreateObservation,
    Medication,
    Observation,
)
from samfhir.domain.models.patient import Patient, PatientSummary
from samfhir.domain.ports.fhir_port import FhirPort


def _safe_coding(codeable_concept: dict | None) -> tuple[str, str]:
    """Extract (code, display) from a CodeableConcept, defaulting to 'unknown'."""
    if not codeable_concept:
        return ("unknown", "unknown")
    codings = codeable_concept.get("coding") or []
    if not codings:
        return ("unknown", codeable_concept.get("text", "unknown"))
    first = codings[0]
    return (first.get("code", "unknown"), first.get("display", "unknown"))


def _safe_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except (ValueError, TypeError):
        return None


def _map_patient(data: dict) -> Patient:
    names = data.get("name") or []
    first_name = names[0] if names else {}
    family = first_name.get("family", "Unknown")
    givens = first_name.get("given") or []
    given = givens[0] if givens else "Unknown"
    return Patient(
        id=data["id"],
        family_name=family,
        given_name=given,
        birth_date=_safe_date(data.get("birthDate")) or date(1900, 1, 1),
        gender=data.get("gender", "unknown"),
    )


def _map_condition(data: dict) -> Condition:
    code, display = _safe_coding(data.get("code"))
    status_code, _ = _safe_coding(data.get("clinicalStatus"))
    return Condition(
        id=data.get("id", "unknown"),
        code=code,
        display=display,
        clinical_status=status_code,
        onset_date=_safe_date(data.get("onsetDateTime")),
    )


def _map_observation(data: dict) -> Observation:
    code, display = _safe_coding(data.get("code"))
    vq = data.get("valueQuantity") or {}
    value = str(vq["value"]) if "value" in vq else data.get("valueString", "")
    unit = vq.get("unit")
    return Observation(
        id=data.get("id", "unknown"),
        code=code,
        display=display,
        value=value,
        unit=unit,
        effective_date=_safe_date(data.get("effectiveDateTime")),
    )


def _map_medication(data: dict) -> Medication:
    code, display = _safe_coding(data.get("medicationCodeableConcept"))
    return Medication(
        id=data.get("id", "unknown"),
        code=code,
        display=display,
        status=data.get("status", "unknown"),
        authored_on=_safe_date(data.get("authoredOn")),
    )


def _map_allergy(data: dict) -> Allergy:
    code, display = _safe_coding(data.get("code"))
    status_code, _ = _safe_coding(data.get("clinicalStatus"))
    return Allergy(
        id=data.get("id", "unknown"),
        code=code,
        display=display,
        clinical_status=status_code,
        criticality=data.get("criticality"),
    )


_FHIR_ISSUE_TYPE_TO_HTTP: dict[str, int] = {
    "invalid": 400,
    "structure": 400,
    "required": 400,
    "value": 400,
    "invariant": 400,
    "security": 403,
    "login": 401,
    "forbidden": 403,
    "suppressed": 403,
    "not-found": 404,
    "deleted": 410,
    "conflict": 409,
    "duplicate": 409,
    "lock": 423,
    "multiple-matches": 412,
    "not-supported": 422,
    "processing": 500,
    "exception": 500,
    "timeout": 504,
    "throttled": 429,
    "transient": 503,
    "informational": 200,
    "too-costly": 422,
    "business-rule": 422,
    "too-long": 400,
    "code-invalid": 400,
    "extension": 400,
}


def _extract_status_code(exc: OperationOutcome) -> int:
    """Derive an HTTP status code from a fhirpy OperationOutcome's issue type."""
    resource = getattr(exc, "resource", None)
    if resource and isinstance(resource, dict):
        issues = resource.get("issue", [])
        if issues:
            code = issues[0].get("code", "")
            return _FHIR_ISSUE_TYPE_TO_HTTP.get(code, 500)
    return 500


def _extract_operation_outcome_detail(exc: OperationOutcome) -> str:
    """Pull a human-readable message from a fhirpy OperationOutcome exception."""
    resource = getattr(exc, "resource", None)
    if resource and isinstance(resource, dict):
        issues = resource.get("issue", [])
        if issues:
            return issues[0].get("diagnostics", str(exc))
        text = resource.get("text", {})
        if isinstance(text, dict):
            return text.get("div", str(exc))
    return str(exc)


async def _handle_fhir_errors(coro, patient_id: str):
    try:
        return await coro
    except ResourceNotFound:
        raise PatientNotFoundError(patient_id)
    except OperationOutcome as exc:
        raise FhirServerError(
            status_code=_extract_status_code(exc),
            detail=_extract_operation_outcome_detail(exc),
        ) from exc
    except aiohttp.ClientError as exc:
        raise ConnectionError(f"FHIR server unreachable: {exc}") from exc


LOINC_SYSTEM_URI = "http://loinc.org"
SNOMED_SYSTEM_URI = "http://snomed.info/sct"
CONDITION_CLINICAL_STATUS_SYSTEM_URI = (
    "http://terminology.hl7.org/CodeSystem/condition-clinical"
)


class HapiFhirClient(FhirPort):
    def __init__(self, base_url: str) -> None:
        self._client = AsyncFHIRClient(url=base_url)

    async def get_patient(self, patient_id: str) -> Patient:
        ref = self._client.reference("Patient", patient_id)
        resource = await _handle_fhir_errors(ref.to_resource(), patient_id)
        return _map_patient(resource)

    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        patient = await self.get_patient(patient_id)
        conditions, observations, medications, allergies = await asyncio.gather(
            self.search_conditions(patient_id),
            self.search_observations(patient_id),
            self.search_medications(patient_id),
            self.search_allergies(patient_id),
        )
        active_conditions = [c for c in conditions if c.clinical_status == "active"]
        active_medications = [m for m in medications if m.status == "active"]
        return PatientSummary(
            patient=patient,
            active_conditions=active_conditions,
            recent_observations=observations,
            active_medications=active_medications,
            allergies=allergies,
        )

    async def _search(self, resource_type: str, patient_id: str) -> list[dict]:
        resources = (
            self._client.resources(resource_type).search(patient=patient_id).limit(100)
        )
        return await _handle_fhir_errors(resources.fetch(), patient_id)

    async def search_conditions(self, patient_id: str) -> list[Condition]:
        entries = await self._search("Condition", patient_id)
        return [_map_condition(e) for e in entries]

    async def search_observations(self, patient_id: str) -> list[Observation]:
        entries = await self._search("Observation", patient_id)
        return [_map_observation(e) for e in entries]

    async def search_medications(self, patient_id: str) -> list[Medication]:
        entries = await self._search("MedicationRequest", patient_id)
        return [_map_medication(e) for e in entries]

    async def search_allergies(self, patient_id: str) -> list[Allergy]:
        entries = await self._search("AllergyIntolerance", patient_id)
        return [_map_allergy(e) for e in entries]

    async def create_observation(self, observation: CreateObservation) -> Observation:
        resource_data: dict = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": LOINC_SYSTEM_URI,
                        "code": observation.code,
                        "display": observation.display,
                    }
                ]
            },
            "subject": {"reference": f"Patient/{observation.patient_id}"},
            "valueQuantity": {
                "value": float(observation.value),
                "unit": observation.unit,
            },
        }
        if observation.effective_date is not None:
            resource_data["effectiveDateTime"] = observation.effective_date.isoformat()
        result = await _handle_fhir_errors(
            self._client.resource("Observation", **resource_data).save(),
            observation.patient_id,
        )
        return _map_observation(result)

    async def create_condition(self, condition: CreateCondition) -> Condition:
        resource_data: dict = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": CONDITION_CLINICAL_STATUS_SYSTEM_URI,
                        "code": condition.clinical_status,
                    }
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": SNOMED_SYSTEM_URI,
                        "code": condition.code,
                        "display": condition.display,
                    }
                ]
            },
            "subject": {"reference": f"Patient/{condition.patient_id}"},
        }
        if condition.onset_date is not None:
            resource_data["onsetDateTime"] = condition.onset_date.isoformat()
        result = await _handle_fhir_errors(
            self._client.resource("Condition", **resource_data).save(),
            condition.patient_id,
        )
        return _map_condition(result)

    async def search_patients(self, name: str | None = None) -> list[Patient]:
        search = self._client.resources("Patient")
        if name:
            search = search.search(name=name)
        search = search.limit(100)
        try:
            entries = await search.fetch()
        except OperationOutcome as exc:
            raise FhirServerError(
                status_code=_extract_status_code(exc),
                detail=_extract_operation_outcome_detail(exc),
            ) from exc
        except aiohttp.ClientError as exc:
            raise ConnectionError(f"FHIR server unreachable: {exc}") from exc
        return [_map_patient(e) for e in entries]
