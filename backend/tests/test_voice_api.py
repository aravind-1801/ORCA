import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_voice_synthesize_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test empty text error handling
        r_empty = await client.post("/api/voice/synthesize", json={"text": "", "language": "en"})
        assert r_empty.status_code == 200
        d_empty = r_empty.json()
        assert d_empty["success"] is False
        assert d_empty["error"]["code"] == "EMPTY_TEXT"

        # Test valid text synthesis call
        r_synth = await client.post("/api/voice/synthesize", json={"text": "Sea is calm today.", "language": "en"})
        assert r_synth.status_code == 200
        d_synth = r_synth.json()
        assert d_synth["provider"] == "fish_audio"
        # If Fish Audio API returned audio bytes, audio_base64 is present
        if d_synth["success"]:
            assert d_synth["audio_base64"] is not None
            assert d_synth["audio_format"] == "mp3"


@pytest.mark.asyncio
async def test_voice_transcribe_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test empty audio error handling
        r_empty = await client.post("/api/voice/transcribe", data={"language": "en"})
        assert r_empty.status_code == 200
        d_empty = r_empty.json()
        assert d_empty["success"] is False
        assert d_empty["error"]["code"] == "EMPTY_AUDIO"
