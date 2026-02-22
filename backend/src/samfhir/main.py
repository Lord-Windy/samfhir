from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from samfhir.adapters.inbound.api import fhir_router, health_router, patient_router
from samfhir.adapters.outbound.redis_cache import RedisCache
from samfhir.adapters.outbound.hapi_fhir_client import HapiFhirClient
from samfhir.config import Settings
from samfhir.domain.models.errors import FhirServerError, PatientNotFoundError
from samfhir.domain.services.patient_service import PatientService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.cache = RedisCache(app.state.redis)
    app.state.fhir_client = HapiFhirClient(settings.fhir_base_url)
    app.state.patient_service = PatientService(app.state.fhir_client, app.state.cache)
    try:
        yield
    finally:
        await app.state.redis.aclose()


def _register_exception_handlers(application: FastAPI) -> None:
    @application.exception_handler(PatientNotFoundError)
    async def patient_not_found_handler(
        request: Request, exc: PatientNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": "patient_not_found", "patient_id": exc.patient_id},
        )

    @application.exception_handler(FhirServerError)
    async def fhir_server_error_handler(
        request: Request, exc: FhirServerError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=502,
            content={"error": "fhir_server_error", "detail": exc.detail},
        )

    @application.exception_handler(ConnectionError)
    async def connection_error_handler(
        request: Request, exc: ConnectionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={"error": "fhir_server_unavailable"},
        )


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

    _register_exception_handlers(application)

    application.include_router(health_router)
    application.include_router(patient_router)
    application.include_router(fhir_router)

    return application


app = create_app()
