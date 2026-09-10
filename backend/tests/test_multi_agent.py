import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.agents.orchestrator import orchestrator
from backend.app.schemas.orca import OrcaQueryRequest
from backend.app.schemas.common import SafetyStatus


@pytest.mark.asyncio
async def test_orca_query_flow():
    """Test full multi-agent query flow matching Phase 24 & 50"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "Is it safe to go fishing today?",
            "language": "en",
            "latitude": 8.88,
            "longitude": 76.59,
        }
        response = await client.post("/api/v1/orca/query", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert "query_id" in data
        assert data["status"] == "safe"
        assert "Conditions are safe today" in data["answer"]
        assert "Recommended zone" in data["answer"]
        assert data["recommended_zone"]["distance_km"] == 12.0
        assert data["recommended_zone"]["direction"] == "Southwest"
        assert data["weather"]["risk"] == "low"
        assert data["ocean"]["condition"] == "favorable"
        assert data["safety"]["status"] == "safe"
        assert data["data_mode"] == "demo"
        assert data["malayalam_echo"] is not None

        # Test Why ORCA explanation endpoint for this query_id
        q_id = data["query_id"]
        exp_res = await client.get(f"/api/v1/orca/explanation/{q_id}")
        assert exp_res.status_code == 200
        exp_data = exp_res.json()
        assert exp_data["verdict"] == "Clear to Sail"
        assert exp_data["confidence_pct"] >= 95
        assert len(exp_data["agents"]) == 4

        agent_names = [a["agent_name"] for a in exp_data["agents"]]
        assert "Weather Agent" in agent_names
        assert "Ocean Agent" in agent_names
        assert "Fishing-Zone Agent" in agent_names
        assert "Safety Agent" in agent_names


@pytest.mark.asyncio
async def test_multi_agent_safety_precedence():
    """Safety Agent / hazard warnings must take precedence over high fishing potential"""
    from backend.app.agents.weather_agent import weather_agent
    from backend.app.agents.safety_agent import safety_agent
    from backend.app.agents.ocean_agent import ocean_agent
    from backend.app.agents.fishing_zone_agent import fishing_zone_agent

    # Hazardous weather
    w_out = await weather_agent.execute({"wind_kmh": 48.0, "wave_m": 3.0, "rain": "Heavy"})
    o_out = await ocean_agent.execute({"sea_surface_temperature_c": 28.4, "chlorophyll_density": "High", "ocean_current_knots": 0.4})
    s_out = await safety_agent.execute(w_out, o_out, [])

    # Even though ocean has high chlorophyll / fishing opportunity, safety must be DANGER
    assert w_out.status == SafetyStatus.DANGER
    assert s_out.status == SafetyStatus.DANGER
