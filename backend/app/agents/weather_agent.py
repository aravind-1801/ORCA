from typing import Dict, Any
from backend.app.schemas.orca import WeatherAgentOutput
from backend.app.schemas.common import SafetyStatus
from backend.app.config import settings


class WeatherAgent:
    """
    Evaluates atmospheric, wind, wave, and surface squall risks.
    """

    async def execute(self, weather_data: Dict[str, Any]) -> WeatherAgentOutput:
        wind = weather_data.get("wind_kmh", 14.0)
        wave = weather_data.get("wave_m", 0.8)
        rain = str(weather_data.get("rain", "Low"))

        factors = [
            f"Wind {wind:.0f} km/h",
            f"Wave {wave:.1f} m",
            f"Rain {rain}",
        ]

        if wave >= settings.SAFETY_WAVE_DANGER_M or wind >= settings.SAFETY_WIND_DANGER_KMH:
            risk = "high"
            status = SafetyStatus.DANGER
            factors.append("Severe squall/gale hazard detected")
            conf = 0.98
        elif wave >= settings.SAFETY_WAVE_CAUTION_M or wind >= settings.SAFETY_WIND_CAUTION_KMH:
            risk = "moderate"
            status = SafetyStatus.CAUTION
            factors.append("Cautionary sea state")
            conf = 0.94
        else:
            risk = "low"
            status = SafetyStatus.SAFE
            factors.append("No squall or cyclone activity detected")
            conf = 0.95

        return WeatherAgentOutput(
            risk_level=risk,
            status=status,
            key_factors=factors,
            confidence=conf,
        )


weather_agent = WeatherAgent()
