import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app


@pytest.mark.asyncio
async def test_location_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Get current location
        res = await client.get("/api/location")
        assert res.status_code == 200
        data = res.json()
        assert "location_name" in data
        assert "latitude" in data
        assert "longitude" in data

        # 2. Update location to Kochi
        update_payload = {
            "location_name": "Kochi Coast",
            "harbor": "Cochin Fisheries Harbor",
            "latitude": 9.93,
            "longitude": 76.26,
            "state": "Kerala",
        }
        put_res = await client.put("/api/location", json=update_payload)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert updated["location_name"] == "Kochi Coast"
        assert updated["latitude"] == 9.93

        # Reset back to Kollam
        await client.put("/api/location", json={
            "location_name": "Kollam Coast",
            "harbor": "Neendakara Harbor",
            "latitude": 8.88,
            "longitude": 76.59,
        })


@pytest.mark.asyncio
async def test_weather_and_ocean_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Weather
        w_res = await client.get("/api/weather?lat=8.88&lon=76.59")
        assert w_res.status_code == 200
        w_data = w_res.json()
        assert "wind_kmh" in w_data
        assert "wave_m" in w_data
        assert "water_temp_c" in w_data

        # Ocean
        o_res = await client.get("/api/ocean?lat=8.88&lon=76.59")
        assert o_res.status_code == 200
        o_data = o_res.json()
        assert "sea_surface_temperature_c" in o_data
        assert "chlorophyll_density" in o_data


@pytest.mark.asyncio
async def test_fishing_zones_and_map_data():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Zones
        z_res = await client.get("/api/fishing-zones?lat=8.88&lon=76.59")
        assert z_res.status_code == 200
        z_data = z_res.json()
        assert "zones" in z_data
        assert len(z_data["zones"]) > 0
        zone_id = z_data["zones"][0]["id"]

        # Zone detail
        detail_res = await client.get(f"/api/fishing-zones/{zone_id}?lat=8.88&lon=76.59")
        assert detail_res.status_code == 200

        # Map data
        map_res = await client.get("/api/map/data?lat=8.88&lon=76.59")
        assert map_res.status_code == 200
        map_data = map_res.json()
        assert "vessel" in map_data
        assert "recommended_zone" in map_data
        assert "navigation_route" in map_data
        assert "isobaths" in map_data


@pytest.mark.asyncio
async def test_ai_chat_and_languages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # English
        en_res = await client.post("/api/ai/chat", json={
            "query": "Is it safe to fish today?",
            "language": "en",
        })
        assert en_res.status_code == 200
        en_data = en_res.json()
        assert "response" in en_data
        assert len(en_data["response"]) > 0

        # Tamil
        ta_res = await client.post("/api/ai/chat", json={
            "query": "இன்று கடலுக்கு செல்லலாமா?",
            "language": "ta",
        })
        assert ta_res.status_code == 200
        ta_data = ta_res.json()
        assert "response" in ta_data
        assert any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in ta_data["response"])

        # Malayalam
        ml_res = await client.post("/api/ai/chat", json={
            "query": "ഇന്ന് മീൻപിടിക്കാൻ പോകാമോ?",
            "language": "ml",
        })
        assert ml_res.status_code == 200
        ml_data = ml_res.json()
        assert "response" in ml_data
        assert any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in ml_data["response"])


@pytest.mark.asyncio
async def test_profile_and_language_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Language API
        lang_res = await client.get("/api/language")
        assert lang_res.status_code == 200

        put_lang = await client.put("/api/language", json={"language": "ta"})
        assert put_lang.status_code == 200
        assert put_lang.json()["language"] == "ta"

        # Profile API
        prof_res = await client.get("/api/profile")
        assert prof_res.status_code == 200
        prof_data = prof_res.json()
        assert "name" in prof_data

        # Update profile
        update_res = await client.put("/api/profile", json={
            "name": "Ayub Chettiyar Skipper",
            "vessel_name": "Sea King II Pro",
        })
        assert update_res.status_code == 200
        assert update_res.json()["name"] == "Ayub Chettiyar Skipper"

        # Profile image
        img_res = await client.post("/api/profile/image", json={
            "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        })
        assert img_res.status_code == 200
        assert img_res.json()["status"] == "success"
