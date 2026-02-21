from datetime import date
from typing import Any

import httpx
import pytest
from fastapi import FastAPI

from samfhir.adapters.inbound.api import fhir_router, health_router, patient_router
from samfhir.adapters.outbound.stub_fhir_client import StubFhirClient
from samfhir.config import Settings
from samfhir.domain.models.observation import Allergy, Condition, Medication, Observation
from samfhir.domain.models.patient import Patient, PatientSummary
from samfhir.domain.ports.cache_port import CachePort
from samfhir.domain.ports.fhir_port import FhirPort
from samfhir.domain.services.patient_service import PatientService


class MockFhirPort(FhirPort):
    """In-memory FhirPort with call tracking for unit tests."""

    def __init__(self) -> None:
        self.call_count: dict[str, int] = {}
        self._patient = Patient(
            id="test-123",
            family_name="Test",
            given_name="Patient",
            birth_date=date(1990, 1, 1),
            gender="male",
        )
        self._conditions = [
            Condition(
                id="c1", code="44054006", display="Diabetes",
                clinical_status="active", onset_date=date(2020, 1, 1),
            ),
        ]
        self._observations = [
            Observation(
                id="o1", code="8480-6", display="BP Systolic",
                value="120", unit="mmHg", effective_date=date(2024, 1, 1),
            ),
        ]
        self._medications = [
            Medication(
                id="m1", code="861007", display="Metformin",
                status="active", authored_on=date(2023, 1, 1),
            ),
        ]
        self._allergies = [
            Allergy(
                id="a1", code="763875007", display="Penicillin",
                clinical_status="active", criticality="high",
            ),
        ]

    def _track(self, method: str) -> None:
        self.call_count[method] = self.call_count.get(method, 0) + 1

    async def get_patient(self, patient_id: str) -> Patient:
        self._track("get_patient")
        return self._patient

    async def get_patient_summary(self, patient_id: str) -> PatientSummary:
        self._track("get_patient_summary")
        return PatientSummary(
            patient=self._patient,
            active_conditions=self._conditions,
            recent_observations=self._observations,
            active_medications=self._medications,
            allergies=self._allergies,
        )

    async def search_conditions(self, patient_id: str) -> list[Condition]:
        self._track("search_conditions")
        return self._conditions

    async def search_observations(self, patient_id: str) -> list[Observation]:
        self._track("search_observations")
        return self._observations

    async def search_medications(self, patient_id: str) -> list[Medication]:
        self._track("search_medications")
        return self._medications

    async def search_allergies(self, patient_id: str) -> list[Allergy]:
        self._track("search_allergies")
        return self._allergies


class MockCachePort(CachePort):
    """In-memory CachePort with hit/miss tracking."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._hits = 0
        self._misses = 0

    async def get(self, key: str) -> str | None:
        val = self._store.get(key)
        if val is not None:
            self._hits += 1
        else:
            self._misses += 1
        return val

    async def set(self, key: str, value: str, ttl: int = 300) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def flush(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0

    async def stats(self) -> dict[str, Any]:
        return {"hits": self._hits, "misses": self._misses}

    async def health_check(self) -> bool:
        return True


class _MockRedis:
    """Minimal mock supporting ping() for health endpoint tests."""

    async def ping(self) -> bool:
        return True


@pytest.fixture
def mock_fhir_port() -> MockFhirPort:
    return MockFhirPort()


@pytest.fixture
def mock_cache_port() -> MockCachePort:
    return MockCachePort()


@pytest.fixture
async def test_client(mock_cache_port: MockCachePort):
    app = FastAPI()
    app.state.settings = Settings()
    app.state.redis = _MockRedis()
    app.state.cache = mock_cache_port
    app.state.fhir_client = StubFhirClient()
    app.state.patient_service = PatientService(
        app.state.fhir_client, app.state.cache,
    )
    app.include_router(health_router)
    app.include_router(patient_router)
    app.include_router(fhir_router)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
