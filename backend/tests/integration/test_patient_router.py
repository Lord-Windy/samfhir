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


async def test_create_observation_returns_201(test_client: httpx.AsyncClient):
    resp = await test_client.post(
        "/api/v1/observations",
        json={
            "patient_id": PATIENT_ID,
            "code": "8867-4",
            "display": "Heart rate",
            "value": "72",
            "unit": "bpm",
            "effective_date": "2024-06-01",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "8867-4"
    assert data["display"] == "Heart rate"
    assert data["value"] == "72"
    assert data["unit"] == "bpm"
    assert data["effective_date"] == "2024-06-01"
    assert data["id"]  # server-assigned


async def test_create_observation_minimal(test_client: httpx.AsyncClient):
    resp = await test_client.post(
        "/api/v1/observations",
        json={
            "patient_id": PATIENT_ID,
            "code": "8867-4",
            "display": "Heart rate",
            "value": "72",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["unit"] is None
    assert data["effective_date"] is None


async def test_create_condition_returns_201(test_client: httpx.AsyncClient):
    resp = await test_client.post(
        "/api/v1/conditions",
        json={
            "patient_id": PATIENT_ID,
            "code": "73211009",
            "display": "Diabetes mellitus",
            "clinical_status": "active",
            "onset_date": "2023-03-15",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["code"] == "73211009"
    assert data["display"] == "Diabetes mellitus"
    assert data["clinical_status"] == "active"
    assert data["onset_date"] == "2023-03-15"
    assert data["id"]


async def test_create_condition_defaults(test_client: httpx.AsyncClient):
    resp = await test_client.post(
        "/api/v1/conditions",
        json={
            "patient_id": PATIENT_ID,
            "code": "73211009",
            "display": "Diabetes mellitus",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["clinical_status"] == "active"
    assert data["onset_date"] is None


async def test_create_observation_invalid_patient_returns_404(
    test_client: httpx.AsyncClient,
):
    resp = await test_client.post(
        "/api/v1/observations",
        json={
            "patient_id": "nonexistent-id",
            "code": "8867-4",
            "display": "Heart rate",
            "value": "72",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "patient_not_found"


async def test_create_observation_missing_fields_returns_422(
    test_client: httpx.AsyncClient,
):
    resp = await test_client.post(
        "/api/v1/observations",
        json={
            "patient_id": PATIENT_ID,
            "code": "8867-4",
            "display": "Heart rate",
        },
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


async def test_create_condition_missing_fields_returns_422(
    test_client: httpx.AsyncClient,
):
    resp = await test_client.post(
        "/api/v1/conditions",
        json={
            "patient_id": PATIENT_ID,
        },
    )
    assert resp.status_code == 422
    assert "detail" in resp.json()


async def test_create_condition_invalid_patient_returns_404(
    test_client: httpx.AsyncClient,
):
    resp = await test_client.post(
        "/api/v1/conditions",
        json={
            "patient_id": "nonexistent-id",
            "code": "73211009",
            "display": "Diabetes mellitus",
        },
    )
    assert resp.status_code == 404
    assert resp.json()["error"] == "patient_not_found"
