import os

import pytest

pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_DB_TESTS", "0") == "1",
    reason="Database tests disabled",
)


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "database" in body


@pytest.mark.asyncio
async def test_dashboard_metrics_endpoint(client, merchant_id):
    if merchant_id is None:
        pytest.skip("No seeded merchant in database")
    response = await client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    body = response.json()
    assert "revenue_at_risk" in body
    assert "recovery_rate" in body


@pytest.mark.asyncio
async def test_transactions_list_endpoint(client, merchant_id):
    if merchant_id is None:
        pytest.skip("No seeded merchant in database")
    response = await client.get("/api/transactions?page=1&page_size=10")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body


@pytest.mark.asyncio
async def test_policies_endpoint(client, merchant_id):
    if merchant_id is None:
        pytest.skip("No seeded merchant in database")
    response = await client.get("/api/policies")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_audit_endpoint(client):
    response = await client.get("/api/audit?page=1&page_size=5")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body


@pytest.mark.asyncio
async def test_simulation_endpoint(client):
    response = await client.post(
        "/api/simulations/run",
        json={"amount": 250, "currency": "USD", "risk_profile": "medium"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "baseline" in body
    assert "candidates" in body


@pytest.mark.asyncio
async def test_not_found_transaction(client):
    response = await client.get(
        "/api/transactions/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_validation_error_format(client):
    response = await client.post(
        "/api/simulations/run",
        json={"amount": -1, "currency": "USD", "risk_profile": "medium"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
