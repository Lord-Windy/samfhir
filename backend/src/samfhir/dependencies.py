from fastapi import Request

from samfhir.config import Settings
from samfhir.domain.ports.cache_port import CachePort
from samfhir.domain.ports.fhir_port import FhirPort
from samfhir.domain.services.patient_service import PatientService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_redis(request: Request):  # noqa: ANN201
    return request.app.state.redis


def get_cache(request: Request) -> CachePort:
    return request.app.state.cache


def get_fhir_client(request: Request) -> FhirPort:
    return request.app.state.fhir_client


def get_patient_service(request: Request) -> PatientService:
    return request.app.state.patient_service
