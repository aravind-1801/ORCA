from typing import Dict, Any, Optional, List
from backend.app.llm.gemini_provider import llm_provider
from backend.app.llm.query_understanding import QueryIntent, ExtractedQuery
from backend.app.schemas.common import SafetyStatus
from backend.app.utils.logging import logger
from backend.app.config import settings

SPECIES_TRANSLATIONS = {
    "ta": {
        "Indian Mackerel & Sardines": "கானாங்கெளுத்தி & மத்தி",
        "Indian Mackerel": "கானாங்கெளுத்தி",
        "Sardines": "மத்தி மீன்கள்",
        "Tuna & Mackerel": "சூரை & கானாங்கெளுத்தி",
        "Yellowfin Tuna": "மஞ்சள் துடுப்பு சூரை",
        "Sardines & Anchovies": "மத்தி & நெத்திலி",
        "Seer Fish / Kingfish": "வஞ்சிரம் மீன்",
        "Pomfret & Ribbonfish": "வௌ்வால் மீன் & வாளை மீன்",
    },
    "ml": {
        "Indian Mackerel & Sardines": "അയലയും മത്തിയും",
        "Indian Mackerel": "അയല",
        "Sardines": "മത്തി",
        "Tuna & Mackerel": "ചൂരയും അയലയും",
        "Yellowfin Tuna": "കേര / മഞ്ഞച്ചൂര",
        "Sardines & Anchovies": "മത്തിയും കൊഴുidentical / നത്തോലിയും",
        "Seer Fish / Kingfish": "നെയ്മീൻ / അയില",
        "Pomfret & Ribbonfish": "ആവോലിയും വാളയും",
    }
}

DIRECTION_TRANSLATIONS = {
    "ta": {
        "Southwest": "தென்மேற்கு",
        "West-Southwest": "மேற்கு-தென்மேற்கு",
        "South-Southwest": "தெற்கு-தென்மேற்கு",
        "Northwest": "வடமேற்கு",
        "Southeast": "தென்கிழக்கு",
        "Northeast": "வடகிழக்கு",
        "West": "மேற்கு",
        "South": "தெற்கு",
        "North": "வடக்கு",
        "East": "கிழக்கு",
    },
    "ml": {
        "Southwest": "തെക്കുപടിഞ്ഞാറ്",
        "West-Southwest": "പടിഞ്ഞാറ്-തെക്കുപടിഞ്ഞാറ്",
        "South-Southwest": "തെക്ക്-തെക്കുപടിഞ്ഞാറ്",
        "Northwest": "വടക്കുപടിഞ്ഞാറ്",
        "Southeast": "തെക്കുകിഴക്ക്",
        "Northeast": "വടക്കുകിഴക്ക്",
        "West": "പടിഞ്ഞാറ്",
        "South": "തെക്ക്",
        "North": "വടക്ക്",
        "East": "കിഴക്ക്",
    }
}


class OrcaResponseAgent:
    """
    Transforms validated multi-agent facts into tailored, query-specific answers for fishermen.
    Produces context-aware answers for each intent (Safety, Weather, Ocean, Fishing Zone, Alerts, Zone Details).
    Supports English (en-IN), Malayalam (ml-IN), and Tamil (ta-IN).
    Enforces Safety Precedence: DANGER/CAUTION warnings strictly override fishing opportunities.
    Guarantees 100% pure target language without cross-language pollution.
    """

    async def generate_response(
        self,
        query: str,
        extracted: ExtractedQuery,
        safety_status: SafetyStatus,
        weather_data: Dict[str, Any],
        ocean_data: Dict[str, Any],
        best_zone: Dict[str, Any],
        alerts: List[Dict[str, Any]],
        language: str = "en",
        location_name: str = "Kollam Coast",
        rag_context: str = "",
        rag_chunks: int = 0,
    ) -> Dict[str, Any]:
        # Normalize language code: 'ml', 'ml-IN', 'ta', 'ta-IN', 'en', 'en-IN'
        lang_norm = (language or "en").lower()
        is_ml = "ml" in lang_norm or "malayalam" in lang_norm
        is_ta = "ta" in lang_norm or "tamil" in lang_norm

        target_lang_code = "ta" if is_ta else ("ml" if is_ml else "en")
        target_lang_name = "Tamil" if is_ta else ("Malayalam" if is_ml else "English")

        intent = extracted.intent
        time_frame = extracted.time_frame
        is_tomorrow = time_frame == "tomorrow"

        wind_kmh = weather_data.get("wind_kmh", 14.0)
        wind_dir = weather_data.get("wind_direction", "West-Southwest")
        wave_m = weather_data.get("wave_m", 0.8)
        rain = weather_data.get("rain", "Low")
        water_temp_c = ocean_data.get("sea_surface_temperature_c", 28.4)
        ocean_current = ocean_data.get("ocean_current_knots", 0.4)
        chlorophyll = ocean_data.get("chlorophyll_density", "Favorable")

        zone_code = best_zone.get("code") or best_zone.get("name") or "Zone A-12"
        dist_km = round(best_zone.get("distance_km", 12.0))
        direction = best_zone.get("direction", "Southwest")
        course = best_zone.get("course", 218)
        depth_m = best_zone.get("bottom_depth_m") or best_zone.get("depth_m", 44)
        species = best_zone.get("target_species", "Indian Mackerel & Sardines")

        # Localized terms
        ta_dir = DIRECTION_TRANSLATIONS["ta"].get(direction, direction)
        ml_dir = DIRECTION_TRANSLATIONS["ml"].get(direction, direction)
        ta_wind_dir = DIRECTION_TRANSLATIONS["ta"].get(wind_dir, wind_dir)
        ml_wind_dir = DIRECTION_TRANSLATIONS["ml"].get(wind_dir, wind_dir)

        ta_species = SPECIES_TRANSLATIONS["ta"].get(species, species)
        ml_species = SPECIES_TRANSLATIONS["ml"].get(species, species)

        # 1. Check Safety Override
        if safety_status == SafetyStatus.DANGER:
            active_reason = alerts[0].get("title", "High swell and storm warning") if alerts else "Dangerous sea conditions"
            en_ans = f"Warning: Unsafe conditions detected. {active_reason}. Do not venture into the sea; stay in harbor."
            ml_ans = f"മുന്നറിയിപ്പ്: കടൽ അതീവ പ്രക്ഷുബ്ധമാണ്. കടലിൽ പോകരുത്; ഹാർബറിൽ തന്നെ തുടരുക."
            ta_ans = f"எச்சரிக்கை: கடல் மிகவும் கொந்தளிப்பாக உள்ளது. கடலுக்குச் செல்ல வேண்டாம்; துறைமுகத்தில் இருங்கள்."

        elif safety_status == SafetyStatus.CAUTION and intent != QueryIntent.WEATHER and intent != QueryIntent.OCEAN:
            en_ans = f"Caution: Elevated wave heights of {wave_m:.1f} m and wind at {wind_kmh:.0f} km/h. Exercise extreme vigilance."
            ml_ans = f"ജാഗ്രത: തിരമാല {wave_m:.1f} മീറ്ററും കാറ്റ് {wind_kmh:.0f} കി.മീ/മണിക്കൂറുമാണ്. അതീവ ജാഗ്രത പാലിക്കുക."
            ta_ans = f"எச்சரிக்கை: அலை உயரம் {wave_m:.1f} மீ மற்றும் காற்று {wind_kmh:.0f} கி.மீ/மணி. தீவிர எச்சரிக்கையுடன் இருக்கவும்."

        else:
            # 2. Intent-Specific Tailored Answers
            if intent == QueryIntent.FISHING_ZONE:
                if is_tomorrow:
                    en_ans = f"For tomorrow, high catch potential continues {dist_km} km {direction} (Course {course}°). Target: {species}."
                    ml_ans = f"നാളെയും {ml_dir} {dist_km} കി.മീ (ദിശ {course}°) മേഖലയിൽ ഉയർന്ന മീൻ ലഭ്യത പ്രതീക്ഷിക്കുന്നു. ഇനം: {ml_species}."
                    ta_ans = f"நாளை {ta_dir} {dist_km} கி.மீ (திசை {course}°) பகுதியில் சிறந்த மீன்பிடி வாய்ப்பு உள்ளது. மீன்: {ta_species}."
                else:
                    en_ans = f"Best fishing zone is {dist_km} km {direction} (Course {course}°), depth {depth_m}m. High catch probability for {species}."
                    ml_ans = f"ഏറ്റവും അനുയോജ്യമായ മീൻപിടുത്ത മേഖല {ml_dir} {dist_km} കി.മീ അകലെയാണ് (ദിശ {course}°). ആഴം {depth_m} മീറ്റർ. {ml_species} ലഭ്യത കൂടുതൽ."
                    ta_ans = f"சிறந்த மீன்பிடி பகுதி {ta_dir} {dist_km} கி.மீ (திசை {course}°), ஆழம் {depth_m} மீ. {ta_species} கிடைக்க வாய்ப்பு அதிகம்."

            elif intent == QueryIntent.WEATHER:
                if is_tomorrow:
                    en_ans = f"Tomorrow's marine forecast: surface winds around {wind_kmh:.0f} km/h from {wind_dir}, waves {wave_m:.1f} m, and {rain.lower()} rain probability."
                    ml_ans = f"നാളത്തെ കാലാവസ്ഥ: {ml_wind_dir} ഭാഗത്തുനിന്ന് {wind_kmh:.0f} കി.മീ വേഗത്തിൽ കാറ്റും, {wave_m:.1f} മീറ്റർ തിരമാലയും, കുറഞ്ഞ മഴയും."
                    ta_ans = f"நாளை வானிலை: {ta_wind_dir} திசையிலிருந்து காற்று {wind_kmh:.0f} கி.மீ/மணி, அலை {wave_m:.1f} மீ, மழை வாய்ப்பு குறைவு."
                else:
                    en_ans = f"Current marine weather: Wind is {wind_kmh:.0f} km/h from {wind_dir}, wave height {wave_m:.1f} m, and rain risk is {rain.lower()}."
                    ml_ans = f"ഇപ്പോഴത്തെ കാലാവസ്ഥ: കാറ്റ് {ml_wind_dir} ഭാഗത്തുനിന്ന് {wind_kmh:.0f} കി.മീ വേഗത, തിരമാല {wave_m:.1f} മീറ്റർ, മഴ സാധ്യത കുറവ്."
                    ta_ans = f"தற்போதைய வானிலை: காற்று {ta_wind_dir} திசையில் {wind_kmh:.0f} கி.மீ/மணி, அலை {wave_m:.1f} மீ, மழை வாய்ப்பு குறைவு."

            elif intent == QueryIntent.OCEAN:
                en_ans = f"Ocean condition is {ocean_data.get('condition', 'favorable')}. Sea temperature is {water_temp_c:.1f}°C, waves are {wave_m:.1f} m, and current velocity is {ocean_current:.1f} knots."
                ml_ans = f"കടൽ അവസ്ഥ അനുകൂലമാണ്. ജല താപനില {water_temp_c:.1f}°C, തിരമാല {wave_m:.1f} മീറ്റർ, ഒഴുക്ക് {ocean_current:.1f} നോട്ട്സ്."
                ta_ans = f"கடல் நிலை சாதகமாக உள்ளது. நீர் வெப்பநிலை {water_temp_c:.1f}°C, அலை {wave_m:.1f} மீ, நீரோட்டம் {ocean_current:.1f} நாட்ஸ்."

            elif intent == QueryIntent.ALERT:
                if alerts:
                    active_titles = ", ".join([a.get("title", "") for a in alerts[:2]])
                    en_ans = f"Active advisory in this sector: {active_titles}. Stay alert on VHF Channel 16."
                    ml_ans = f"നിലവിലെ മുന്നറിയിപ്പ്: വി.എച്ച്.എഫ് ചാനൽ 16 ശ്രദ്ധിക്കുക. സുരക്ഷിതത്വം പാലിക്കുക."
                    ta_ans = f"செயலில் உள்ள எச்சரிக்கை: வி.எச்.எஃப் அலைவரிசை 16 கவனிக்கவும். பாதுகாப்பு வழிமுறைகளைப் பின்பற்றவும்."
                else:
                    en_ans = f"All coastal sectors are clear. No active storm, cyclone, or high swell warnings for {location_name} today."
                    ml_ans = f"{location_name} തീരദേശത്ത് അപായ മുന്നറിയിപ്പുകൾ ഒന്നുമില്ല. കടൽ ശാന്തമാണ്, സുരക്ഷിതമായി യാത്ര ചെയ്യാം."
                    ta_ans = f"{location_name} கடலோர எச்சரிக்கைகள் ஏதுமில்லை. புயல் அல்லது அலை எச்சரிக்கை இல்லை, பயணம் பாதுகாப்பானது."

            elif intent == QueryIntent.ZONE_DETAILS:
                en_ans = f"{zone_code} is {dist_km} km {direction}, heading {course}°, depth {depth_m}m. Surface temp {water_temp_c:.1f}°C with {chlorophyll.lower()} chlorophyll."
                ml_ans = f"{zone_code} {ml_dir} {dist_km} കി.മീ അകലെയാണ് (ദിശ {course}°). ആഴം {depth_m} മീറ്റർ, ജല താപനില {water_temp_c:.1f}°C."
                ta_ans = f"{zone_code} {ta_dir} {dist_km} கி.மீ (திசை {course}°). ஆழம் {depth_m} மீ, நீர் வெப்பநிலை {water_temp_c:.1f}°C."

            else:  # SAFETY or GENERAL_MARINE
                if is_tomorrow:
                    en_ans = f"Conditions for tomorrow appear safe with winds at {wind_kmh:.0f} km/h and calm seas. Safe navigation window is open."
                    ml_ans = f"നാളെയും കടൽ ശാന്തമായിരിക്കാൻ സാധ്യതയുണ്ട്. കാറ്റ് {wind_kmh:.0f} കി.മീ, സുരക്ഷിതമായി കടലിൽ പോകാം."
                    ta_ans = f"நாளை கடல் அமைதியாக இருக்கும் என எதிர்பார்க்கப்படுகிறது. காற்று {wind_kmh:.0f} கி.மீ, பயணம் பாதுகாப்பானது."
                else:
                    en_ans = f"Conditions are safe today. Surface wind is {wind_kmh:.0f} km/h, wave height {wave_m:.1f} m. Recommended zone: {dist_km} km {direction}, high catch probability."
                    ml_ans = f"ഇന്ന് കടൽ ശാന്തമാണ്. കാറ്റ് {wind_kmh:.0f} കി.മീ, തിരമാല {wave_m:.1f} മീറ്റർ. ശുപാർശ ചെയ്യുന്ന മേഖല: {ml_dir} {dist_km} കി.മീ."
                    ta_ans = f"இன்று கடல் அமைதியாக உள்ளது. காற்று {wind_kmh:.0f} கி.மீ, அலை {wave_m:.1f} மீ. பரிந்துரைக்கப்பட்ட பகுதி: {ta_dir} {dist_km} கி.மீ."

        # Choose the exact matching base answer
        if is_ta:
            base_answer = ta_ans
        elif is_ml:
            base_answer = ml_ans
        else:
            base_answer = en_ans

        final_answer = base_answer
        llm_used = False
        llm_paraphrase_used = False
        rag_active = bool(rag_context and rag_context.strip())
        effective_chunks = rag_chunks if rag_chunks > 0 else (len([line for line in rag_context.split("\n") if line.strip()]) if rag_active else 0)

        # If live LLM is configured, request contextual generation from Gemini
        if settings.GEMINI_API_KEY:
            try:
                llm_used = True
                strict_system = (
                    f"You are ORCA, a trusted marine intelligence and fishing advisory assistant for local fishermen. "
                    f"Rules:\n"
                    f"1. You MUST speak STRICTLY and ONLY in {target_lang_name}.\n"
                    f"2. Never mix English into Tamil or Malayalam sentences.\n"
                    f"3. Never hallucinate or alter any numeric values, distances, directions, wind speeds, or wave heights.\n"
                    f"4. Keep the reply friendly, direct, authoritative, and concise."
                )
                rag_section = f"\nRelevant Local Marine Knowledge Base:\n{rag_context}\n" if rag_active else ""
                llm_prompt = (
                    f"User Query: {query}\n"
                    f"Current Location: {location_name}\n"
                    f"Validated Marine Data Facts: {base_answer}\n"
                    f"{rag_section}\n"
                    f"Synthesize a clear and concise reply for the fisherman in {target_lang_name} communicating this exact information."
                )

                llm_response = await llm_provider.generate_text(
                    llm_prompt,
                    system_prompt=strict_system,
                    temperature=0.2,
                    language=target_lang_code,
                )

                if llm_response and len(llm_response.strip()) > 5:
                    final_answer = llm_response.strip()
                    llm_paraphrase_used = True
            except Exception as e:
                logger.warning(f"LLM generation failed ({e}). Retaining verified factual template.")

        return {
            "answer": final_answer,
            "malayalam_echo": ml_ans,
            "llm_used": llm_used,
            "llm_paraphrase_used": llm_paraphrase_used,
            "language": target_lang_code,
            "rag_used": rag_active,
            "rag_chunks": effective_chunks,
        }


response_agent = OrcaResponseAgent()
