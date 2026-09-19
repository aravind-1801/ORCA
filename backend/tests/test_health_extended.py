import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_extended_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Gemini health
        r_gemini = await client.get("/api/health/gemini")
        assert r_gemini.status_code == 200
        d_gemini = r_gemini.json()
        assert d_gemini["provider"] == "gemini"
        assert "configured" in d_gemini

        # 2. Maps health
        r_maps = await client.get("/api/health/maps")
        assert r_maps.status_code == 200
        d_maps = r_maps.json()
        assert d_maps["provider"] == "Google Maps"
        assert "configured" in d_maps

        # 3. Voice health
        r_voice = await client.get("/api/health/voice")
        assert r_voice.status_code == 200
        d_voice = r_voice.json()
        assert "stt" in d_voice and "tts" in d_voice

        # 4. TTS health
        r_tts = await client.get("/api/health/tts")
        assert r_tts.status_code == 200
        d_tts = r_tts.json()
        assert d_tts["provider"] == "fish_audio"

        # 5. Weather health
        r_weather = await client.get("/api/health/weather")
        assert r_weather.status_code == 200

        # 6. Ocean health
        r_ocean = await client.get("/api/health/ocean")
        assert r_ocean.status_code == 200

        # 7. Redis health
        r_redis = await client.get("/api/health/redis")
        assert r_redis.status_code == 200

        # 8. Dashboard aggregated diagnostics
        r_dash = await client.get("/api/health/dashboard")
        assert r_dash.status_code == 200
        d_dash = r_dash.json()
        assert "gemini" in d_dash
        assert "google_maps" in d_dash
        assert "groq_stt" in d_dash
        assert "fish_audio" in d_dash
        assert "weather" in d_dash
        assert "ocean" in d_dash
