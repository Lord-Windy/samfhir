from datetime import date

from pydantic import BaseModel


class CreateObservationRequest(BaseModel):
    patient_id: str
    code: str
    display: str
    value: str
    unit: str | None = None
    effective_date: date | None = None


class CreateConditionRequest(BaseModel):
    patient_id: str
    code: str
    display: str
    clinical_status: str = "active"
    onset_date: date | None = None


class PatientResponse(BaseModel):
    id: str
    family_name: str
    given_name: str
    birth_date: date
    gender: str


class ConditionResponse(BaseModel):
    id: str
    code: str
    display: str
    clinical_status: str
    onset_date: date | None


class ObservationResponse(BaseModel):
    id: str
    code: str
    display: str
    value: str
    unit: str | None
    effective_date: date | None


class MedicationResponse(BaseModel):
    id: str
    code: str
    display: str
    status: str
    authored_on: date | None


class AllergyResponse(BaseModel):
    id: str
    code: str
    display: str
    clinical_status: str
    criticality: str | None


class PatientSummaryResponse(BaseModel):
    patient: PatientResponse
    active_conditions: list[ConditionResponse]
    recent_observations: list[ObservationResponse]
    active_medications: list[MedicationResponse]
    allergies: list[AllergyResponse]
