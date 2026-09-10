from typing import Dict, Any, List
from backend.app.config import settings
from backend.app.schemas.common import SafetyStatus


class SafetyService:
    """
    Deterministic Safety Rule Engine.
    Evaluates verified physical parameters and active warnings.
    Safety status cannot be relaxed by AI suggestions or catch potential.
    """

    @staticmethod
    def evaluate_safety(
        wave_m: float,
        wind_kmh: float,
        active_alerts: List[Dict[str, Any]],
        ocean_condition: str = "favorable",
    ) -> Dict[str, Any]:
        reasons = []
        status = SafetyStatus.SAFE
        severity = "none"

        # 1. Check active alerts (Highest precedence)
        danger_alerts = [a for a in active_alerts if str(a.get("severity", "")).lower() == "danger"]
        caution_alerts = [a for a in active_alerts if str(a.get("severity", "")).lower() == "caution"]

        if danger_alerts:
            status = SafetyStatus.DANGER
            severity = "high"
            for a in danger_alerts:
                reasons.append(f"Active Alert: {a.get('title', 'Hazard warning active')}")

        elif caution_alerts:
            status = SafetyStatus.CAUTION
            severity = "moderate"
            for a in caution_alerts:
                reasons.append(f"Advisory: {a.get('title', 'Cautionary weather advisory')}")

        # 2. Check deterministic physical wave height thresholds
        if wave_m >= settings.SAFETY_WAVE_DANGER_M:
            status = SafetyStatus.DANGER
            severity = "high"
            reasons.append(f"Excessive wave height: {wave_m}m exceeds {settings.SAFETY_WAVE_DANGER_M}m danger threshold.")
        elif wave_m >= settings.SAFETY_WAVE_CAUTION_M and status != SafetyStatus.DANGER:
            status = SafetyStatus.CAUTION
            severity = "moderate"
            reasons.append(f"Elevated swell: {wave_m}m reaches {settings.SAFETY_WAVE_CAUTION_M}m caution threshold.")

        # 3. Check deterministic physical wind thresholds
        if wind_kmh >= settings.SAFETY_WIND_DANGER_KMH:
            status = SafetyStatus.DANGER
            severity = "high"
            reasons.append(f"Gale force winds: {wind_kmh} km/h exceeds {settings.SAFETY_WIND_DANGER_KMH} km/h danger threshold.")
        elif wind_kmh >= settings.SAFETY_WIND_CAUTION_KMH and status != SafetyStatus.DANGER:
            status = SafetyStatus.CAUTION
            severity = "moderate"
            reasons.append(f"Brisk wind: {wind_kmh} km/h reaches {settings.SAFETY_WIND_CAUTION_KMH} km/h caution threshold.")

        # Default safe reassuring state
        if not reasons:
            reasons.append("Coastal sectors clear. Sea conditions calm and safe for traditional and motorized craft.")

        labels = {
            SafetyStatus.SAFE: ("Safe", "Favorable", "#16A34A"),
            SafetyStatus.CAUTION: ("Caution", "Moderate", "#F59E0B"),
            SafetyStatus.DANGER: ("Danger", "Unsafe", "#DC2626"),
        }
        label, favorable_text, color_hex = labels[status]

        return {
            "status": status,
            "label": label,
            "favorable_text": favorable_text,
            "color_hex": color_hex,
            "severity": severity,
            "reasons": reasons,
            "confidence": 0.98 if status == SafetyStatus.SAFE else 0.99,
        }


safety_service = SafetyService()
