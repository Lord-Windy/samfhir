import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samfhir.domain.models.patient import Patient, PatientSummary
    from samfhir.domain.ports.fhir_port import FhirPort
    from samfhir.domain.ports.cache_port import CachePort


class PatientService:
    def __init__(self, fhir_port: "FhirPort", cache_port: "CachePort", ttl: int = 300):
        self._fhir = fhir_port
        self._cache = cache_port
        self._ttl = ttl

    async def get_patient(self, patient_id: str) -> "Patient":
        cache_key = f"patient:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            from samfhir.domain.models.patient import Patient
            from datetime import datetime

            data = json.loads(cached)
            if isinstance(data.get("birth_date"), str):
                data["birth_date"] = datetime.strptime(
                    data["birth_date"], "%Y-%m-%d"
                ).date()
            return Patient(**data)

        patient = await self._fhir.get_patient(patient_id)
        await self._cache.set(
            cache_key,
            json.dumps(
                {
                    "id": patient.id,
                    "family_name": patient.family_name,
                    "given_name": patient.given_name,
                    "birth_date": patient.birth_date.isoformat(),
                    "gender": patient.gender,
                }
            ),
            self._ttl,
        )
        return patient

    async def get_patient_summary(self, patient_id: str) -> "PatientSummary":
        cache_key = f"patient_summary:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            from samfhir.domain.models.patient import Patient, PatientSummary
            from samfhir.domain.models.observation import (
                Condition,
                Observation,
                Medication,
                Allergy,
            )
            from datetime import datetime

            def parse_date(val):
                if val is None:
                    return None
                return datetime.strptime(val, "%Y-%m-%d").date()

            def parse_condition(data):
                data = data.copy()
                if data.get("onset_date"):
                    data["onset_date"] = parse_date(data["onset_date"])
                return Condition(**data)

            def parse_observation(data):
                data = data.copy()
                if data.get("effective_date"):
                    data["effective_date"] = parse_date(data["effective_date"])
                return Observation(**data)

            def parse_medication(data):
                data = data.copy()
                if data.get("authored_on"):
                    data["authored_on"] = parse_date(data["authored_on"])
                return Medication(**data)

            data = json.loads(cached)
            patient_data = data["patient"]
            patient_data["birth_date"] = parse_date(patient_data["birth_date"])
            return PatientSummary(
                patient=Patient(**patient_data),
                active_conditions=[
                    parse_condition(c) for c in data["active_conditions"]
                ],
                recent_observations=[
                    parse_observation(o) for o in data["recent_observations"]
                ],
                active_medications=[
                    parse_medication(m) for m in data["active_medications"]
                ],
                allergies=[Allergy(**a) for a in data["allergies"]],
            )

        summary = await self._fhir.get_patient_summary(patient_id)

        def serialize_condition(c):
            return {
                "id": c.id,
                "code": c.code,
                "display": c.display,
                "clinical_status": c.clinical_status,
                "onset_date": c.onset_date.isoformat() if c.onset_date else None,
            }

        def serialize_observation(o):
            return {
                "id": o.id,
                "code": o.code,
                "display": o.display,
                "value": o.value,
                "unit": o.unit,
                "effective_date": o.effective_date.isoformat()
                if o.effective_date
                else None,
            }

        def serialize_medication(m):
            return {
                "id": m.id,
                "code": m.code,
                "display": m.display,
                "status": m.status,
                "authored_on": m.authored_on.isoformat() if m.authored_on else None,
            }

        def serialize_allergy(a):
            return {
                "id": a.id,
                "code": a.code,
                "display": a.display,
                "clinical_status": a.clinical_status,
                "criticality": a.criticality,
            }

        await self._cache.set(
            cache_key,
            json.dumps(
                {
                    "patient": {
                        "id": summary.patient.id,
                        "family_name": summary.patient.family_name,
                        "given_name": summary.patient.given_name,
                        "birth_date": summary.patient.birth_date.isoformat(),
                        "gender": summary.patient.gender,
                    },
                    "active_conditions": [
                        serialize_condition(c) for c in summary.active_conditions
                    ],
                    "recent_observations": [
                        serialize_observation(o) for o in summary.recent_observations
                    ],
                    "active_medications": [
                        serialize_medication(m) for m in summary.active_medications
                    ],
                    "allergies": [serialize_allergy(a) for a in summary.allergies],
                }
            ),
            self._ttl,
        )
        return summary

    async def invalidate_patient_cache(self, patient_id: str) -> None:
        await self._cache.delete(f"patient:{patient_id}")
        await self._cache.delete(f"patient_summary:{patient_id}")
