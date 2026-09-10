import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_profile_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET profile
        res = await client.get("/api/v1/profile")
        assert res.status_code == 200
        p = res.json()
        assert p["name"] == "Ayub Chettiyar"
        assert p["vessel_name"] == "Sea King II"
        assert p["registration_no"] == "KL-02-F-491"

        # PATCH profile language
        patch_res = await client.patch("/api/v1/profile", json={"preferred_language": "en"})
        assert patch_res.status_code == 200
        updated = patch_res.json()
        assert updated["preferred_language"] == "en"

        # Restore back to ml
        await client.patch("/api/v1/profile", json={"preferred_language": "ml"})
