import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.llm.query_understanding import query_engine, QueryIntent


@pytest.mark.asyncio
async def test_query_understanding_intents():
    # Test intent extraction
    assert query_engine.understand_query("Is it safe to go fishing today?").intent == QueryIntent.SAFETY
    assert query_engine.understand_query("Where is the best fishing zone?").intent == QueryIntent.FISHING_ZONE
    assert query_engine.understand_query("What is the surface wind and weather?").intent == QueryIntent.WEATHER
    assert query_engine.understand_query("What is the wave height and sea condition?").intent == QueryIntent.OCEAN
    assert query_engine.understand_query("Any active storm or cyclone warnings?").intent == QueryIntent.ALERT
    assert query_engine.understand_query("Tell me about Zone A-12").intent == QueryIntent.ZONE_DETAILS


@pytest.mark.asyncio
async def test_conversational_follow_up():
    conv_id = "test_conv_123"
    # Query 1
    q1 = query_engine.understand_query("Is it safe today?", conversation_id=conv_id)
    assert q1.intent == QueryIntent.SAFETY
    assert q1.time_frame == "today"

    # Query 2 (Follow-up)
    q2 = query_engine.understand_query("What about tomorrow?", conversation_id=conv_id)
    assert q2.intent == QueryIntent.SAFETY
    assert q2.time_frame == "tomorrow"


@pytest.mark.asyncio
async def test_different_questions_produce_different_answers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Question 1: Weather
        r_weather = await client.post("/api/v1/orca/query", json={"query": "What is the weather today?", "language": "en"})
        assert r_weather.status_code == 200
        d_weather = r_weather.json()
        assert d_weather["intent"] == "WEATHER"
        assert "wind" in d_weather["answer"].lower()

        # Question 2: Fishing zone
        r_zone = await client.post("/api/v1/orca/query", json={"query": "Where is the best fishing zone?", "language": "en"})
        assert r_zone.status_code == 200
        d_zone = r_zone.json()
        assert d_zone["intent"] == "FISHING_ZONE"
        assert "best fishing zone" in d_zone["answer"].lower() or "zone" in d_zone["answer"].lower()

        # Question 3: Alerts
        r_alert = await client.post("/api/v1/orca/query", json={"query": "Any warnings today?", "language": "en"})
        assert r_alert.status_code == 200
        d_alert = r_alert.json()
        assert d_alert["intent"] == "ALERT"
        assert "warning" in d_alert["answer"].lower() or "clear" in d_alert["answer"].lower()

        # Check answers are distinct
        assert d_weather["answer"] != d_zone["answer"]
        assert d_zone["answer"] != d_alert["answer"]


@pytest.mark.asyncio
async def test_multilingual_query_answers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Malayalam
        r_ml = await client.post("/api/v1/orca/query", json={"query": "ഇന്ന് മീൻപിടിക്കാൻ പോകാമോ?", "language": "ml"})
        assert r_ml.status_code == 200
        d_ml = r_ml.json()
        assert any(char in d_ml["answer"] for char in ["ക", "ട", "ൽ", "ശ", "ാ", "ന"])

        # Tamil
        r_ta = await client.post("/api/v1/orca/query", json={"query": "மீன்பிடிக்க செல்லலாமா?", "language": "ta"})
        assert r_ta.status_code == 200
        d_ta = r_ta.json()
        assert any(char in d_ta["answer"] for char in ["க", "ட", "ல", "அ", "ம", "ை"])
