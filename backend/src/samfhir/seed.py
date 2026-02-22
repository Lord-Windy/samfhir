import asyncio
from datetime import date

from fhirpy import AsyncFHIRClient

from samfhir.config import Settings


JASON_ARGONAUT_PATIENT = {
    "resourceType": "Patient",
    "id": None,
    "identifier": [
        {"system": "urn:oid:1.2.840.114350.1.13.327.1.7.5.737384.4", "value": "2"}
    ],
    "name": [{"family": "Argonaut", "given": ["Jason"]}],
    "birthDate": "1985-01-01",
    "gender": "male",
    "active": True,
}

TEST_CONDITIONS = [
    {
        "code": "38341003",
        "display": "Hypertension",
        "clinical_status": "active",
        "onset_date": date(2020, 1, 15),
    },
    {
        "code": "44054006",
        "display": "Type 2 diabetes mellitus",
        "clinical_status": "active",
        "onset_date": date(2019, 6, 20),
    },
]

TEST_OBSERVATIONS = [
    {
        "code": "8480-6",
        "display": "Systolic blood pressure",
        "value": "120",
        "unit": "mmHg",
        "effective_date": date(2024, 1, 10),
    },
    {
        "code": "8462-4",
        "display": "Diastolic blood pressure",
        "value": "80",
        "unit": "mmHg",
        "effective_date": date(2024, 1, 10),
    },
    {
        "code": "4548-4",
        "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
        "value": "7.2",
        "unit": "%",
        "effective_date": date(2024, 1, 10),
    },
]

TEST_MEDICATIONS = [
    {
        "code": "309362",
        "display": "lisinopril 10 MG Oral Tablet",
        "status": "active",
    },
    {
        "code": "860975",
        "display": "metformin hydrochloride 500 MG Oral Tablet",
        "status": "active",
    },
]

TEST_ALLERGIES = [
    {
        "code": "763875007",
        "display": "Product containing sulfonamide",
        "clinical_status": "active",
        "criticality": "high",
    },
    {
        "code": "91935009",
        "display": "Allergy to peanuts",
        "clinical_status": "active",
        "criticality": "high",
    },
]

SNOMED_SYSTEM = "http://snomed.info/sct"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
LOINC_SYSTEM = "http://loinc.org"
CLINICAL_STATUS_SYSTEM = "http://terminology.hl7.org/CodeSystem/condition-clinical"
ALLERGY_CLINICAL_STATUS_SYSTEM = (
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
)


async def seed_hapi(base_url: str | None = None) -> str:
    settings = Settings()
    fhir_base = base_url or settings.fhir_base_url
    client = AsyncFHIRClient(url=fhir_base)

    patient_data = JASON_ARGONAUT_PATIENT.copy()
    del patient_data["id"]
    patient_resource = client.resource("Patient", **patient_data)
    await patient_resource.save()
    patient_id = patient_resource["id"]
    print(f"Created patient: {patient_id}")

    for cond in TEST_CONDITIONS:
        condition_data = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {"system": CLINICAL_STATUS_SYSTEM, "code": cond["clinical_status"]}
                ]
            },
            "code": {
                "coding": [
                    {
                        "system": SNOMED_SYSTEM,
                        "code": cond["code"],
                        "display": cond["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
        }
        if cond["onset_date"]:
            condition_data["onsetDateTime"] = cond["onset_date"].isoformat()
        await client.resource("Condition", **condition_data).save()
        print(f"  Created condition: {cond['display']}")

    for obs in TEST_OBSERVATIONS:
        obs_data = {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [
                    {
                        "system": LOINC_SYSTEM,
                        "code": obs["code"],
                        "display": obs["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "valueQuantity": {"value": float(obs["value"]), "unit": obs["unit"]},
        }
        if obs["effective_date"]:
            obs_data["effectiveDateTime"] = obs["effective_date"].isoformat()
        await client.resource("Observation", **obs_data).save()
        print(f"  Created observation: {obs['display']}")

    for med in TEST_MEDICATIONS:
        med_data = {
            "resourceType": "MedicationRequest",
            "status": med["status"],
            "medicationCodeableConcept": {
                "coding": [
                    {
                        "system": RXNORM_SYSTEM,
                        "code": med["code"],
                        "display": med["display"],
                    }
                ]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "intent": "order",
        }
        await client.resource("MedicationRequest", **med_data).save()
        print(f"  Created medication: {med['display']}")

    for allergy in TEST_ALLERGIES:
        allergy_data = {
            "resourceType": "AllergyIntolerance",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": ALLERGY_CLINICAL_STATUS_SYSTEM,
                        "code": allergy["clinical_status"],
                    }
                ]
            },
            "criticality": allergy["criticality"],
            "code": {
                "coding": [
                    {
                        "system": SNOMED_SYSTEM,
                        "code": allergy["code"],
                        "display": allergy["display"],
                    }
                ]
            },
            "patient": {"reference": f"Patient/{patient_id}"},
        }
        await client.resource("AllergyIntolerance", **allergy_data).save()
        print(f"  Created allergy: {allergy['display']}")

    print("\nSeeding complete!")
    print(f"Patient ID: {patient_id}")
    return patient_id


async def main():
    patient_id = await seed_hapi()
    print(
        f"\nTest with: curl http://localhost:8000/api/v1/patients/{patient_id}/summary"
    )


if __name__ == "__main__":
    asyncio.run(main())
