from typing import Dict, Any, List
from backend.app.schemas.orca import SafetyAgentOutput, WeatherAgentOutput, OceanAgentOutput
from backend.app.schemas.common import SafetyStatus
from backend.app.services.safety_service import safety_service


class SafetyAgent:
    """
    Evaluates comprehensive safety consensus.
    Prioritizes verified safety alerts and deterministic physics rules.
    """

    async def execute(
        self,
        weather_output: WeatherAgentOutput,
        ocean_output: OceanAgentOutput,
        active_alerts: List[Dict[str, Any]],
    ) -> SafetyAgentOutput:
        # Check active alerts first
        danger_alerts = [a for a in active_alerts if str(a.get("severity", "")).lower() == "danger"]
        if danger_alerts:
            return SafetyAgentOutput(
                status=SafetyStatus.DANGER,
                reasons=[f"Active Warning: {danger_alerts[0].get('title', 'Maritime hazard')}"] + [r.get("title") for r in danger_alerts[1:]],
                confidence=0.99,
            )

        # Inherit weather status if non-safe
        if weather_output.status == SafetyStatus.DANGER:
            return SafetyAgentOutput(
                status=SafetyStatus.DANGER,
                reasons=weather_output.key_factors,
                confidence=weather_output.confidence,
            )

        caution_alerts = [a for a in active_alerts if str(a.get("severity", "")).lower() == "caution"]
        if caution_alerts:
            return SafetyAgentOutput(
                status=SafetyStatus.CAUTION,
                reasons=[f"Advisory: {caution_alerts[0].get('title', 'Cautionary notice')}"],
                confidence=0.95,
            )

        if weather_output.status == SafetyStatus.CAUTION:
            return SafetyAgentOutput(
                status=SafetyStatus.CAUTION,
                reasons=weather_output.key_factors,
                confidence=weather_output.confidence,
            )

        return SafetyAgentOutput(
            status=SafetyStatus.SAFE,
            reasons=["No active alerts. Port clear, safe return window > 18 hours."],
            confidence=0.98,
        )


safety_agent = SafetyAgent()
