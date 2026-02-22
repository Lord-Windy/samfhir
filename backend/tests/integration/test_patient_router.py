import httpx

from samfhir.adapters.outbound.stub_fhir_client import StubFhirClient

PATIENT_ID = StubFhirClient.JASON_ARGONAUT_ID


async def test_health_returns_ok(test_client: httpx.AsyncClient):
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["redis"] == "connected"


async def test_patient_endpoint_returns_json(test_client: httpx.AsyncClient):
    resp = await test_client.get(f"/api/v1/patients/{PATIENT_ID}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == PATIENT_ID
    assert data["family_name"] == "Argonaut"
    assert data["given_name"] == "Jason"
    assert data["birth_date"] == "1975-12-25"
    assert data["gender"] == "male"


async def test_cache_stats_reflect_hits(test_client: httpx.AsyncClient):
    # First request — cache miss
    await test_client.get(f"/api/v1/patients/{PATIENT_ID}")
    # Second request — cache hit
    await test_client.get(f"/api/v1/patients/{PATIENT_ID}")

    resp = await test_client.get("/api/v1/cache/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["hits"] >= 1


async def test_cache_flush_clears_data(test_client: httpx.AsyncClient):
    # Populate cache
    await test_client.get(f"/api/v1/patients/{PATIENT_ID}")

    # Flush
    resp = await test_client.delete("/api/v1/cache")
    assert resp.status_code == 200
    assert resp.json()["status"] == "flushed"

    # Stats reset to zero
    resp = await test_client.get("/api/v1/cache/stats")
    stats = resp.json()
    assert stats["hits"] == 0
    assert stats["misses"] == 0


async def test_patient_not_found_returns_404(test_client: httpx.AsyncClient):
    resp = await test_client.get("/api/v1/patients/nonexistent-id")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "patient_not_found"
    assert data["patient_id"] == "nonexistent-id"


async def test_patient_summary_not_found_returns_404(test_client: httpx.AsyncClient):
    resp = await test_client.get("/api/v1/patients/nonexistent-id/summary")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "patient_not_found"


async def test_conditions_not_found_returns_404(test_client: httpx.AsyncClient):
    resp = await test_client.get("/api/v1/patients/nonexistent-id/conditions")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "patient_not_found"
