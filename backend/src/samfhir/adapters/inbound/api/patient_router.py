from fastapi import APIRouter, Depends, Request

from samfhir.adapters.inbound.api.schemas import (
    AllergyResponse,
    ConditionResponse,
    MedicationResponse,
    ObservationResponse,
    PatientResponse,
    PatientSummaryResponse,
)
from samfhir.domain.models.observation import (
    Allergy,
    Condition,
    Medication,
    Observation,
)
from samfhir.domain.models.patient import Patient, PatientSummary
from samfhir.domain.services.patient_service import PatientService

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


def _patient_to_response(patient: Patient) -> PatientResponse:
    return PatientResponse(
        id=patient.id,
        family_name=patient.family_name,
        given_name=patient.given_name,
        birth_date=patient.birth_date,
        gender=patient.gender,
    )


def _condition_to_response(condition: Condition) -> ConditionResponse:
    return ConditionResponse(
        id=condition.id,
        code=condition.code,
        display=condition.display,
        clinical_status=condition.clinical_status,
        onset_date=condition.onset_date,
    )


def _observation_to_response(observation: Observation) -> ObservationResponse:
    return ObservationResponse(
        id=observation.id,
        code=observation.code,
        display=observation.display,
        value=observation.value,
        unit=observation.unit,
        effective_date=observation.effective_date,
    )


def _medication_to_response(medication: Medication) -> MedicationResponse:
    return MedicationResponse(
        id=medication.id,
        code=medication.code,
        display=medication.display,
        status=medication.status,
        authored_on=medication.authored_on,
    )


def _allergy_to_response(allergy: Allergy) -> AllergyResponse:
    return AllergyResponse(
        id=allergy.id,
        code=allergy.code,
        display=allergy.display,
        clinical_status=allergy.clinical_status,
        criticality=allergy.criticality,
    )


def _summary_to_response(summary: PatientSummary) -> PatientSummaryResponse:
    return PatientSummaryResponse(
        patient=_patient_to_response(summary.patient),
        active_conditions=[
            _condition_to_response(c) for c in summary.active_conditions
        ],
        recent_observations=[
            _observation_to_response(o) for o in summary.recent_observations
        ],
        active_medications=[
            _medication_to_response(m) for m in summary.active_medications
        ],
        allergies=[_allergy_to_response(a) for a in summary.allergies],
    )


def get_patient_service(request: Request) -> PatientService:
    return request.app.state.patient_service


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> PatientResponse:
    patient = await service.get_patient(patient_id)
    return _patient_to_response(patient)


@router.get("/{patient_id}/summary", response_model=PatientSummaryResponse)
async def get_patient_summary(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> PatientSummaryResponse:
    summary = await service.get_patient_summary(patient_id)
    return _summary_to_response(summary)


@router.get("/{patient_id}/conditions", response_model=list[ConditionResponse])
async def get_patient_conditions(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> list[ConditionResponse]:
    summary = await service.get_patient_summary(patient_id)
    return [_condition_to_response(c) for c in summary.active_conditions]


@router.get("/{patient_id}/observations", response_model=list[ObservationResponse])
async def get_patient_observations(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> list[ObservationResponse]:
    summary = await service.get_patient_summary(patient_id)
    return [_observation_to_response(o) for o in summary.recent_observations]


@router.get("/{patient_id}/medications", response_model=list[MedicationResponse])
async def get_patient_medications(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> list[MedicationResponse]:
    summary = await service.get_patient_summary(patient_id)
    return [_medication_to_response(m) for m in summary.active_medications]


@router.get("/{patient_id}/allergies", response_model=list[AllergyResponse])
async def get_patient_allergies(
    patient_id: str,
    service: PatientService = Depends(get_patient_service),
) -> list[AllergyResponse]:
    summary = await service.get_patient_summary(patient_id)
    return [_allergy_to_response(a) for a in summary.allergies]
