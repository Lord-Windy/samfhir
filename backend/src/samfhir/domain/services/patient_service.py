import dataclasses
import json
from datetime import date

from samfhir.domain.models.observation import (
    Allergy,
    Condition,
    CreateCondition,
    CreateObservation,
    Medication,
    Observation,
)
from samfhir.domain.models.patient import Patient, PatientSummary
from samfhir.domain.ports.cache_port import CachePort
from samfhir.domain.ports.fhir_port import FhirPort


def _date_default(obj: object) -> str:
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Not JSON serializable: {type(obj)}")


def _dumps(obj: object) -> str:
    return json.dumps(dataclasses.asdict(obj), default=_date_default)


def _from_dict[T](cls: type[T], data: dict) -> T:
    """Reconstruct a flat dataclass from a dict, parsing ISO date strings."""
    kwargs = {}
    for f in dataclasses.fields(cls):
        val = data[f.name]
        if val is not None and _is_date_field(f):
            val = date.fromisoformat(val)
        kwargs[f.name] = val
    return cls(**kwargs)


def _is_date_field(f: dataclasses.Field) -> bool:
    tp = f.type
    if tp is date:
        return True
    return hasattr(tp, "__args__") and date in tp.__args__


class PatientService:
    def __init__(self, fhir_port: FhirPort, cache_port: CachePort, ttl: int = 300):
        self._fhir = fhir_port
        self._cache = cache_port
        self._ttl = ttl

    async def get_patient(self, patient_id: str) -> Patient:
        cache_key = f"patient:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return _from_dict(Patient, json.loads(cached))
        patient = await self._fhir.get_patient(patient_id)
        await self._cache.set(cache_key, _dumps(patient), self._ttl)
        return patient

    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        cache_key = f"patient_summary:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            data = json.loads(cached)
            return PatientSummary(
                patient=_from_dict(Patient, data["patient"]),
                active_conditions=[
                    _from_dict(Condition, c) for c in data["active_conditions"]
                ],
                recent_observations=[
                    _from_dict(Observation, o) for o in data["recent_observations"]
                ],
                active_medications=[
                    _from_dict(Medication, m) for m in data["active_medications"]
                ],
                allergies=[_from_dict(Allergy, a) for a in data["allergies"]],
            )
        summary = await self._fhir.get_patient_summary(patient_id)
        await self._cache.set(cache_key, _dumps(summary), self._ttl)
        return summary

    async def search_conditions(self, patient_id: str) -> list[Condition]:
        cache_key = f"conditions:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return [_from_dict(Condition, c) for c in json.loads(cached)]
        conditions = await self._fhir.search_conditions(patient_id)
        await self._cache.set(
            cache_key,
            json.dumps(
                [dataclasses.asdict(c) for c in conditions], default=_date_default
            ),
            self._ttl,
        )
        return conditions

    async def search_observations(self, patient_id: str) -> list[Observation]:
        cache_key = f"observations:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return [_from_dict(Observation, o) for o in json.loads(cached)]
        observations = await self._fhir.search_observations(patient_id)
        await self._cache.set(
            cache_key,
            json.dumps(
                [dataclasses.asdict(o) for o in observations], default=_date_default
            ),
            self._ttl,
        )
        return observations

    async def search_medications(self, patient_id: str) -> list[Medication]:
        cache_key = f"medications:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return [_from_dict(Medication, m) for m in json.loads(cached)]
        medications = await self._fhir.search_medications(patient_id)
        await self._cache.set(
            cache_key,
            json.dumps(
                [dataclasses.asdict(m) for m in medications], default=_date_default
            ),
            self._ttl,
        )
        return medications

    async def search_allergies(self, patient_id: str) -> list[Allergy]:
        cache_key = f"allergies:{patient_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return [_from_dict(Allergy, a) for a in json.loads(cached)]
        allergies = await self._fhir.search_allergies(patient_id)
        await self._cache.set(
            cache_key,
            json.dumps(
                [dataclasses.asdict(a) for a in allergies], default=_date_default
            ),
            self._ttl,
        )
        return allergies

    async def create_observation(self, observation: CreateObservation) -> Observation:
        result = await self._fhir.create_observation(observation)
        await self.invalidate_patient_cache(observation.patient_id)
        return result

    async def create_condition(self, condition: CreateCondition) -> Condition:
        result = await self._fhir.create_condition(condition)
        await self.invalidate_patient_cache(condition.patient_id)
        return result

    async def invalidate_patient_cache(self, patient_id: str) -> None:
        await self._cache.delete(f"patient:{patient_id}")
        await self._cache.delete(f"patient_summary:{patient_id}")
        await self._cache.delete(f"conditions:{patient_id}")
        await self._cache.delete(f"observations:{patient_id}")
        await self._cache.delete(f"medications:{patient_id}")
        await self._cache.delete(f"allergies:{patient_id}")
