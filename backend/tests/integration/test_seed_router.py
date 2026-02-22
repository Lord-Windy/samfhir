from unittest.mock import AsyncMock, patch

import httpx


async def test_seed_returns_403_when_not_debug(test_client: httpx.AsyncClient):
    resp = await test_client.post("/api/v1/seed")
    assert resp.status_code == 403
    assert "debug mode" in resp.json()["detail"]


async def test_seed_returns_201_when_debug(test_client: httpx.AsyncClient):
    # Enable debug mode on the app settings
    test_client._transport.app.state.settings.debug = True  # type: ignore[union-attr]

    with patch(
        "samfhir.adapters.inbound.api.seed_router.seed_hapi",
        new_callable=AsyncMock,
        return_value="test-patient-123",
    ) as mock_seed:
        resp = await test_client.post("/api/v1/seed")

    assert resp.status_code == 201
    data = resp.json()
    assert data["patient_id"] == "test-patient-123"
    assert "seeded successfully" in data["message"]
    mock_seed.assert_awaited_once()
