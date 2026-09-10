import re
from enum import Enum
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from backend.app.llm.gemini_provider import llm_provider
from backend.app.utils.logging import logger


class QueryIntent(str, Enum):
    SAFETY = "SAFETY"
    WEATHER = "WEATHER"
    OCEAN = "OCEAN"
    FISHING_ZONE = "FISHING_ZONE"
    ALERT = "ALERT"
    ZONE_DETAILS = "ZONE_DETAILS"
    GENERAL_MARINE = "GENERAL_MARINE"


class ExtractedQuery(BaseModel):
    intent: QueryIntent = QueryIntent.SAFETY
    time_frame: str = "today"  # 'today' | 'tomorrow' | 'tonight' | 'future'
    target_location: str = "Kollam Coast"
    target_zone_id: Optional[str] = None
    language: str = "en"
    raw_query: str


# Conversation context memory keyed by conversation_id
_CONVERSATION_HISTORY: Dict[str, Dict[str, Any]] = {}


class QueryUnderstandingEngine:
    """
    Analyzes natural language queries from fishermen in English, Malayalam, or Tamil.
    Extracts structured intent, timeframe, location, and entities.
    Maintains multi-turn conversational context for follow-up questions.
    """

    def understand_query(
        self,
        query: str,
        language: str = "en",
        conversation_id: Optional[str] = None,
        default_location: str = "Kollam Coast",
    ) -> ExtractedQuery:
        q_clean = query.strip()
        q_lower = q_clean.lower()

        # Check previous context for follow-up questions
        prev_context = _CONVERSATION_HISTORY.get(conversation_id) if conversation_id else None

        # 1. Detect Timeframe
        time_frame = "today"
        if any(w in q_lower for w in ["tomorrow", "നാളത്തെ", "നാളെ", "நாளை", "நாளைக்கு"]):
            time_frame = "tomorrow"
        elif any(w in q_lower for w in ["tonight", "ഇന്ന് രാത്രി", "രാത്രി", "இரவு"]):
            time_frame = "tonight"
        elif any(w in q_lower for w in ["weekend", "next week", "അടുത്ത ആഴ്ച", "அடுத்த வாரம்"]):
            time_frame = "future"
        elif prev_context and any(w in q_lower for w in ["what about", "how about", "and", "പിന്നെ"]):
            # Inherit previous timeframe if not overridden
            time_frame = prev_context.get("time_frame", "today")

        # 2. Detect Specific Zone ID if present (e.g. A12, B04, C09, Zone A-12)
        zone_match = re.search(r"\b([a-cA-C])[- ]?([0-9]{1,2})\b", q_clean)
        target_zone_id = None
        if zone_match:
            letter, num = zone_match.groups()
            target_zone_id = f"{letter.upper()}{int(num):02d}"

        # 3. Detect Intent
        intent = None

        # Zone details intent
        if target_zone_id or any(w in q_lower for w in ["tell me about zone", "zone details", "മേഖലയുടെ വിവരങ്ങൾ", "பகுதி விவரங்கள்"]):
            intent = QueryIntent.ZONE_DETAILS

        # Warning / Alert intent
        elif any(w in q_lower for w in [
            "warning", "alert", "danger", "cyclone", "storm",
            "മുന്നറിയിപ്പ്", "അപകടം", "ചുഴലിക്കാറ്റ്", "കാറ്റ് മുന്നറിയിപ്പ്",
            "எச்சரிக்கை", "புயல்", "ஆபத்து"
        ]):
            intent = QueryIntent.ALERT

        # Ocean / Wave / Swell intent
        elif any(w in q_lower for w in [
            "wave", "swell", "sea condition", "water temp", "current", "tide", "kinematics",
            "തിരമാല", "തിര", "കടൽക്ഷോഭം", "കടൽ അവസ്ഥ", "അടിഒഴുക്ക്", "വെള്ളത്തിന്റെ ചൂട്",
            "அலை", "கடல் நிலை", "நீரோட்டம்"
        ]):
            intent = QueryIntent.OCEAN

        # Weather / Wind / Rain intent
        elif any(w in q_lower for w in [
            "weather", "wind", "rain", "breeze", "squall", "cloud",
            "കാലാവസ്ഥ", "കാറ്റ്", "മഴ", "കാറ്റിന്റെ വേഗത",
            "வானிலை", "காற்று", "மழை"
        ]):
            intent = QueryIntent.WEATHER

        # Fishing zone / Fish catch intent
        elif any(w in q_lower for w in [
            "fishing zone", "fish zone", "best zone", "where is fish", "catch fish", "where to fish", "how far", "distance",
            "മീൻ ലഭ്യത", "മീൻപിടുത്ത മേഖല", "എവിടെയാണ് മീൻ", "മീൻ എവിടെ", "എത്ര ദൂരം",
            "மீன்பிடி பகுதி", "மீன் எங்கு கிடைக்கும்", "எவ்வளவு தூரம்"
        ]):
            intent = QueryIntent.FISHING_ZONE

        # Safety intent
        elif any(w in q_lower for w in [
            "safe", "safety", "can i go", "can we sail", "is it safe", "go to sea", "harbor", "clear to sail",
            "സുരക്ഷിതമാണോ", "കടലിൽ പോകാമോ", "സുരക്ഷ", "പോകാമോ", "ബോട്ട് ഇറക്കാമോ",
            "பாதுகாப்பானதா", "கடலுக்கு செல்லலாமா", "பாதுகாப்பு"
        ]):
            intent = QueryIntent.SAFETY

        # Handle follow-up queries: e.g. "What about tomorrow?" / "നാളെ എങ്ങനെ?"
        elif prev_context:
            # If the user asks a short follow-up like "tomorrow?" or "and tomorrow?"
            # reuse previous intent with the new timeframe
            intent = prev_context.get("intent", QueryIntent.SAFETY)
        else:
            intent = QueryIntent.SAFETY

        # 4. Detect Location if specified
        target_location = default_location
        for loc in ["kollam", "neendakara", "vizhinjam", "kochi", "munambam", "alappuzha", "trivandrum"]:
            if loc in q_lower:
                target_location = f"{loc.capitalize()} Coast"
                break

        extracted = ExtractedQuery(
            intent=intent,
            time_frame=time_frame,
            target_location=target_location,
            target_zone_id=target_zone_id,
            language=language,
            raw_query=q_clean,
        )

        # Save context for multi-turn conversational follow-up
        if conversation_id:
            _CONVERSATION_HISTORY[conversation_id] = {
                "intent": intent,
                "time_frame": time_frame,
                "target_location": target_location,
                "target_zone_id": target_zone_id,
                "raw_query": q_clean,
            }

        logger.info(f"NLP Query Understanding: Intent={extracted.intent.value}, Time={extracted.time_frame}, Zone={extracted.target_zone_id}")
        return extracted


query_engine = QueryUnderstandingEngine()
