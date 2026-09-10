import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.config import settings
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_check():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "ORCA" in data["service"]
        assert data["demo_mode"] is True


def test_default_gemini_model_is_current():
    assert settings.MODEL_NAME == "gemini-3.6-flash"
