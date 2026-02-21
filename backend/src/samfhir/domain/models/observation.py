from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Condition:
    id: str
    code: str
    display: str
    clinical_status: str
    onset_date: date | None


@dataclass(frozen=True)
class Observation:
    id: str
    code: str
    display: str
    value: str
    unit: str | None
    effective_date: date | None


@dataclass(frozen=True)
class Medication:
    id: str
    code: str
    display: str
    status: str
    authored_on: date | None


@dataclass(frozen=True)
class Allergy:
    id: str
    code: str
    display: str
    clinical_status: str
    criticality: str | None
