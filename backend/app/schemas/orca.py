from datetime import datetime
from typing import List, Optional, Dict, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from backend.app.schemas.common import SafetyStatus, PotentialLevel, DataMode


class OrcaQueryRequest(BaseModel):
    query: str
    language: str = "en"  # 'en' | 'ml' | 'ta' | 'en-IN' | 'ml-IN' | 'ta-IN'
    latitude: Optional[float] = 8.88
    longitude: Optional[float] = 76.59
    conversation_id: Optional[str] = None


class WeatherAgentOutput(BaseModel):
    risk_level: str = "low"  # 'low' | 'moderate' | 'high'
    status: SafetyStatus = SafetyStatus.SAFE
    key_factors: List[str] = ["Wind 14 km/h", "No squall or cyclone detected", "Calm wave 0.8m"]
    confidence: float = 0.95


class OceanAgentOutput(BaseModel):
    condition: str = "favorable"  # 'favorable' | 'moderate' | 'unfavorable'
    key_factors: List[str] = ["SST 28.4°C optimal", "Plankton density rich", "Current velocity 0.4 kt"]
    confidence: float = 0.92


class BestZoneResult(BaseModel):
    id: str = "A12"
    latitude: float = 8.78
    longitude: float = 76.49
    distance_km: float = 12.0
    direction: str = "Southwest"
    potential: str = "high"
    course: int = 218


class FishingZoneAgentOutput(BaseModel):
    best_zone: BestZoneResult
    key_factors: List[str] = ["Frontal boundary convergence", "High pelagic density", "Depth 44m"]
    confidence: float = 0.90


class SafetyAgentOutput(BaseModel):
    status: SafetyStatus = SafetyStatus.SAFE
    reasons: List[str] = ["No active storm warnings", "Harbor and return window open >18 hrs"]
    confidence: float = 0.98


class AgentTrace(BaseModel):
    agent_name: str
    status: str
    verdict: str
    key_factor: str
    latency_ms: int = 45


class OrcaQueryResponse(BaseModel):
    """
    Phase 24 API Contract for POST /api/v1/orca/query
    """
    query_id: str
    status: SafetyStatus = SafetyStatus.SAFE
    intent: str = "SAFETY"
    time_frame: str = "today"
    language: str = "en"
    answer: str
    malayalam_echo: Optional[str] = None
    recommended_zone: Optional[BestZoneResult] = None
    weather: Dict[str, Any] = {"risk": "low", "wind_kmh": 14, "wave_m": 0.8}
    ocean: Dict[str, Any] = {"condition": "favorable", "water_temp_c": 28.4}
    safety: Dict[str, Any] = {"status": "safe", "reasons": ["Sector clear"]}
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_mode: DataMode = DataMode.DEMO
    llm_used: bool = False
    llm_paraphrase_used: bool = False


class AgentSummaryFactor(BaseModel):
    agent_name: str
    subtitle: str
    verdict: str
    summary: str
    status: str = "safe"  # 'safe' | 'caution' | 'danger'
    icon: str = "check_circle"


class OrcaExplanationResponse(BaseModel):
    """
    Phase 22 Why ORCA API Contract
    """
    query_id: str
    verdict: str = "Clear to Sail"
    confidence_pct: int = 98
    consensus_summary: str = "Conditions are safe today. Recommended zone: 12 km southwest with high catch probability."
    agents: List[AgentSummaryFactor]
    data_sources: List[Dict[str, str]] = [
        {"name": "ISRO", "detail": "Oceansat-3", "status": "VERIFIED"},
        {"name": "INCOIS", "detail": "PFZ-Advisory", "status": "VERIFIED"},
        {"name": "IMD", "detail": "Coastal Radar", "status": "VERIFIED"}
    ]
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    data_mode: DataMode = DataMode.DEMO
