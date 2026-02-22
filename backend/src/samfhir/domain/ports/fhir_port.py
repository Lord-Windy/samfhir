from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samfhir.domain.models.patient import Patient, PatientSummary
    from samfhir.domain.models.observation import (
        Condition,
        CreateCondition,
        CreateObservation,
        Observation,
        Medication,
        Allergy,
    )


class FhirPort(ABC):
    @abstractmethod
    async def get_patient(self, patient_id: str) -> "Patient": ...

    @abstractmethod
    async def get_patient_summary(self, patient_id: str) -> "PatientSummary": ...

    @abstractmethod
    async def search_conditions(self, patient_id: str) -> list["Condition"]: ...

    @abstractmethod
    async def search_observations(self, patient_id: str) -> list["Observation"]: ...

    @abstractmethod
    async def search_medications(self, patient_id: str) -> list["Medication"]: ...

    @abstractmethod
    async def search_allergies(self, patient_id: str) -> list["Allergy"]: ...

    @abstractmethod
    async def create_observation(
        self, observation: "CreateObservation"
    ) -> "Observation": ...

    @abstractmethod
    async def create_condition(self, condition: "CreateCondition") -> "Condition": ...
