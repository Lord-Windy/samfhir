from datetime import date

from samfhir.domain.models.observation import (
    Allergy,
    Condition,
    Medication,
    Observation,
)
from samfhir.domain.models.patient import Patient, PatientSummary
from samfhir.domain.ports.fhir_port import FhirPort


class StubFhirClient(FhirPort):
    JASON_ARGONAUT_ID = "Tbt3KUPCSmpToKz7NfYVHA"

    def __init__(self) -> None:
        self._patient = Patient(
            id=self.JASON_ARGONAUT_ID,
            family_name="Argonaut",
            given_name="Jason",
            birth_date=date(1975, 12, 25),
            gender="male",
        )
        self._conditions = [
            Condition(
                id="cond-1",
                code="44054006",
                display="Type 2 diabetes mellitus",
                clinical_status="active",
                onset_date=date(2018, 3, 15),
            ),
            Condition(
                id="cond-2",
                code="38341003",
                display="Hypertension",
                clinical_status="active",
                onset_date=date(2016, 7, 22),
            ),
            Condition(
                id="cond-3",
                code="233604007",
                display="Pneumonia",
                clinical_status="resolved",
                onset_date=date(2020, 1, 10),
            ),
        ]
        self._observations = [
            Observation(
                id="obs-1",
                code="8480-6",
                display="Systolic blood pressure",
                value="138",
                unit="mmHg",
                effective_date=date(2024, 2, 15),
            ),
            Observation(
                id="obs-2",
                code="8462-4",
                display="Diastolic blood pressure",
                value="82",
                unit="mmHg",
                effective_date=date(2024, 2, 15),
            ),
            Observation(
                id="obs-3",
                code="4548-4",
                display="Hemoglobin A1c",
                value="7.2",
                unit="%",
                effective_date=date(2024, 2, 10),
            ),
            Observation(
                id="obs-4",
                code="2345-7",
                display="Glucose",
                value="142",
                unit="mg/dL",
                effective_date=date(2024, 2, 10),
            ),
        ]
        self._medications = [
            Medication(
                id="med-1",
                code="861007",
                display="Metformin 500mg",
                status="active",
                authored_on=date(2023, 6, 1),
            ),
            Medication(
                id="med-2",
                code="309362",
                display="Lisinopril 10mg",
                status="active",
                authored_on=date(2022, 3, 15),
            ),
            Medication(
                id="med-3",
                code="197362",
                display="Aspirin 81mg",
                status="active",
                authored_on=date(2021, 1, 20),
            ),
        ]
        self._allergies = [
            Allergy(
                id="allergy-1",
                code="763875007",
                display="Substance with penicillin structure",
                clinical_status="active",
                criticality="high",
            ),
            Allergy(
                id="allergy-2",
                code="419474003",
                display="Allergy to tree pollen",
                clinical_status="active",
                criticality="low",
            ),
        ]

    async def get_patient(self, patient_id: str) -> Patient:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        return self._patient

    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        active_conditions = [
            c for c in self._conditions if c.clinical_status == "active"
        ]
        return PatientSummary(
            patient=self._patient,
            active_conditions=active_conditions,
            recent_observations=self._observations,
            active_medications=[m for m in self._medications if m.status == "active"],
            allergies=self._allergies,
        )

    async def search_conditions(self, patient_id: str) -> list[Condition]:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        return self._conditions

    async def search_observations(self, patient_id: str) -> list[Observation]:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        return self._observations

    async def search_medications(self, patient_id: str) -> list[Medication]:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        return self._medications

    async def search_allergies(self, patient_id: str) -> list[Allergy]:
        if patient_id != self.JASON_ARGONAUT_ID:
            raise ValueError(f"Patient {patient_id} not found")
        return self._allergies
