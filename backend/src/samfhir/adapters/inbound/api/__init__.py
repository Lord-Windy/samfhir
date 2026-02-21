from samfhir.adapters.inbound.api.fhir_router import router as fhir_router
from samfhir.adapters.inbound.api.health_router import router as health_router
from samfhir.adapters.inbound.api.patient_router import router as patient_router

__all__ = ["fhir_router", "health_router", "patient_router"]
