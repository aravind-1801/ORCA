import pytest
from backend.app.services.safety_service import safety_service
from backend.app.schemas.common import SafetyStatus


def test_safety_clear_conditions():
    eval_result = safety_service.evaluate_safety(
        wave_m=0.8,
        wind_kmh=14.0,
        active_alerts=[],
    )
    assert eval_result["status"] == SafetyStatus.SAFE
    assert eval_result["label"] == "Safe"
    assert eval_result["severity"] == "none"


def test_safety_active_danger_alert_overrides():
    alerts = [
        {
            "id": "alt_cyclone",
            "title": "Severe Cyclone Warning",
            "severity": "danger",
        }
    ]
    eval_result = safety_service.evaluate_safety(
        wave_m=0.8,  # low wave
        wind_kmh=10.0,  # low wind
        active_alerts=alerts,
    )
    assert eval_result["status"] == SafetyStatus.DANGER
    assert eval_result["label"] == "Danger"
    assert any("Severe Cyclone Warning" in r for r in eval_result["reasons"])


def test_safety_high_wave_triggers_danger():
    eval_result = safety_service.evaluate_safety(
        wave_m=3.2,  # exceeds 2.5m danger threshold
        wind_kmh=14.0,
        active_alerts=[],
    )
    assert eval_result["status"] == SafetyStatus.DANGER
    assert any("wave height" in r.lower() for r in eval_result["reasons"])


def test_safety_caution_threshold():
    eval_result = safety_service.evaluate_safety(
        wave_m=1.8,  # between 1.5m and 2.5m
        wind_kmh=14.0,
        active_alerts=[],
    )
    assert eval_result["status"] == SafetyStatus.CAUTION
    assert eval_result["label"] == "Caution"
