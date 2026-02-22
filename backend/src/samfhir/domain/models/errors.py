class PatientNotFoundError(Exception):
    """Raised when a patient cannot be found by ID."""

    def __init__(self, patient_id: str) -> None:
        self.patient_id = patient_id
        super().__init__(f"Patient {patient_id} not found")


class FhirServerError(Exception):
    """Raised when the FHIR server returns an error."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"FHIR server error ({status_code}): {detail}")
