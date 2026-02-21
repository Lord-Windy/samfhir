from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from samfhir.domain.models.observation import (
        Condition,
        Observation,
        Medication,
        Allergy,
    )


@dataclass(frozen=True)
class Patient:
    id: str
    family_name: str
    given_name: str
    birth_date: date
    gender: str


@dataclass(frozen=True)
class PatientSummary:
    patient: Patient
    active_conditions: list["Condition"]
    recent_observations: list["Observation"]
    active_medications: list["Medication"]
    allergies: list["Allergy"]
