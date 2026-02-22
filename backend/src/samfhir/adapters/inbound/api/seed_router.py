from fastapi import APIRouter, HTTPException, Request

from samfhir.config import Settings
from samfhir.seed import seed_hapi

router = APIRouter(prefix="/api/v1", tags=["seed"])


@router.post("/seed", status_code=201)
async def seed_test_data(request: Request):
    settings: Settings = request.app.state.settings
    if not settings.debug:
        raise HTTPException(
            status_code=403,
            detail="Seed endpoint only available in debug mode",
        )

    patient_id = await seed_hapi(settings.fhir_base_url)
    return {"patient_id": patient_id, "message": "Test data seeded successfully"}
