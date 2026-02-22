import asyncio
from datetime import date

import httpx

from samfhir.config import Settings

SNOMED_SYSTEM = "http://snomed.info/sct"
RXNORM_SYSTEM = "http://www.nlm.nih.gov/research/umls/rxnorm"
LOINC_SYSTEM = "http://loinc.org"
CLINICAL_STATUS_SYSTEM = "http://terminology.hl7.org/CodeSystem/condition-clinical"
ALLERGY_CLINICAL_STATUS_SYSTEM = (
    "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
)

JASON_ARGONAUT_PATIENT = {
    "resourceType": "Patient",
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
        "value": 120.0,
        "unit": "mmHg",
        "effective_date": date(2024, 1, 10),
    },
    {
        "code": "8462-4",
        "display": "Diastolic blood pressure",
        "value": 80.0,
        "unit": "mmHg",
        "effective_date": date(2024, 1, 10),
    },
    {
        "code": "4548-4",
        "display": "Hemoglobin A1c/Hemoglobin.total in Blood",
        "value": 7.2,
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


async def _post_resource(
    client: httpx.AsyncClient, base_url: str, resource: dict
) -> dict:
    resp = await client.post(
        f"{base_url}/{resource['resourceType']}",
        json=resource,
        headers={"Content-Type": "application/fhir+json"},
    )
    resp.raise_for_status()
    return resp.json()


async def seed_hapi(base_url: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        result = await _post_resource(client, base_url, JASON_ARGONAUT_PATIENT)
        patient_id = result["id"]
        print(f"Created patient: {patient_id}")

        for cond in TEST_CONDITIONS:
            resource = {
                "resourceType": "Condition",
                "clinicalStatus": {
                    "coding": [
                        {
                            "system": CLINICAL_STATUS_SYSTEM,
                            "code": cond["clinical_status"],
                        }
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
                "onsetDateTime": cond["onset_date"].isoformat(),
            }
            await _post_resource(client, base_url, resource)
            print(f"  Created condition: {cond['display']}")

        for obs in TEST_OBSERVATIONS:
            resource = {
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
                "valueQuantity": {"value": obs["value"], "unit": obs["unit"]},
                "effectiveDateTime": obs["effective_date"].isoformat(),
            }
            await _post_resource(client, base_url, resource)
            print(f"  Created observation: {obs['display']}")

        for med in TEST_MEDICATIONS:
            resource = {
                "resourceType": "MedicationRequest",
                "status": med["status"],
                "intent": "order",
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
            }
            await _post_resource(client, base_url, resource)
            print(f"  Created medication: {med['display']}")

        for allergy in TEST_ALLERGIES:
            resource = {
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
            await _post_resource(client, base_url, resource)
            print(f"  Created allergy: {allergy['display']}")

    print("\nSeeding complete!")
    print(f"Patient ID: {patient_id}")
    return patient_id


async def main():
    settings = Settings()
    patient_id = await seed_hapi(settings.fhir_base_url)
    print(
        f"\nTest with: curl http://localhost:8000/api/v1/patients/{patient_id}/summary"
    )


if __name__ == "__main__":
    asyncio.run(main())
