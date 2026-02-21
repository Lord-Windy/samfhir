from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from samfhir.adapters.inbound.api import fhir_router, health_router, patient_router
from samfhir.adapters.outbound.redis_cache import RedisCache
from samfhir.adapters.outbound.stub_fhir_client import StubFhirClient
from samfhir.config import Settings
from samfhir.domain.services.patient_service import PatientService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.cache = RedisCache(app.state.redis)
    app.state.fhir_client = StubFhirClient()
    app.state.patient_service = PatientService(app.state.fhir_client, app.state.cache)
    try:
        yield
    finally:
        await app.state.redis.aclose()


def create_app() -> FastAPI:
    settings = Settings()
    application = FastAPI(
        title=settings.app_name,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health_router)
    application.include_router(patient_router)
    application.include_router(fhir_router)

    return application


app = create_app()
