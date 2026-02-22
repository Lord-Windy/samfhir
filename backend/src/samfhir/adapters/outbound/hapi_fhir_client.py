import asyncio
from datetime import date

from fhirpy import AsyncFHIRClient
from fhirpy.base.exceptions import OperationOutcome, ResourceNotFound

from samfhir.domain.models.observation import (
    Allergy,
    Condition,
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


class HapiFhirClient(FhirPort):
    def __init__(self, base_url: str) -> None:
        self._client = AsyncFHIRClient(url=base_url)

    async def get_patient(self, patient_id: str) -> Patient:
        try:
            ref = self._client.reference("Patient", patient_id)
            resource = await ref.to_resource()
        except (ResourceNotFound, OperationOutcome) as exc:
            raise ValueError(f"Patient {patient_id} not found") from exc
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
        return await resources.fetch()

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
