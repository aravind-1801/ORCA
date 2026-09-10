import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_marine_status_contract():
    """Verify Phase 51 Sample API Contract for Home status"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marine/status")
        assert response.status_code == 200
        data = response.json()

        # Location
        assert data["location"]["name"] == "Kollam Coast"
        assert data["location"]["latitude"] == 8.88
        assert data["location"]["longitude"] == 76.59

        # Connectivity & Data Mode
        assert data["connectivity"] == "online"
        assert data["data_mode"] == "demo"
        assert "updated_at" in data

        # Safety
        assert data["safety"]["status"] == "safe"
        assert data["safety"]["label"] == "Safe"

        # Weather
        assert data["weather"]["wind_kmh"] == 14.0
        assert data["weather"]["wave_m"] == 0.8
        assert data["weather"]["rain"] == "Low"

        # Best Zone
        assert data["best_zone"]["distance_km"] == 12.0
        assert data["best_zone"]["direction"] == "Southwest"
        assert data["best_zone"]["potential"] == "high"
        assert data["best_zone"]["course"] == 218

        # Recommendation
        assert "Conditions are safe today" in data["recommendation"]["text"]
        assert "12 km southwest" in data["recommendation"]["text"]


@pytest.mark.asyncio
async def test_marine_fishing_zones():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marine/fishing-zones")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data
        assert len(data["zones"]) >= 3
        # First zone should be high potential (A12)
        top = data["zones"][0]
        assert top["id"] == "A12"
        assert top["course_deg"] == 218


@pytest.mark.asyncio
async def test_marine_zone_detail():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marine/fishing-zones/A12")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "A12"
        assert data["bottom_depth_m"] == 44
        assert "Indian Mackerel" in data["target_species"][0]


@pytest.mark.asyncio
async def test_marine_alerts_reassurance():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marine/alerts")
        assert response.status_code == 200
        data = response.json()
        assert data["has_active_alerts"] is False
        assert "clear" in data["status_summary"].lower()


@pytest.mark.asyncio
async def test_marine_data_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/marine/data-status")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 4
        source_names = [s["source_name"] for s in data["sources"]]
        assert any("ISRO" in s for s in source_names)
        assert any("INCOIS" in s for s in source_names)
