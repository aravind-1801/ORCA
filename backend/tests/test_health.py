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


def test_voice_provider_config_keys_are_wired_from_env():
    assert settings.STT_PROVIDER == "groq"
    assert settings.STT_API_KEY.startswith("gsk_")
    assert settings.STT_MODEL == "whisper-large-v3-turbo"
    assert settings.TTS_PROVIDER == "fish_audio"
    assert settings.TTS_API_KEY.startswith("sk-fish-")
    assert settings.TTS_MODEL == "fish-speech-1.5"
