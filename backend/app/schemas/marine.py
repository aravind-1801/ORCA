from datetime import datetime
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from backend.app.schemas.common import SafetyStatus, PotentialLevel, DataMode


class LocationSchema(BaseModel):
    name: str = "Kollam Coast"
    latitude: float = 8.88
    longitude: float = 76.59
    harbor: Optional[str] = "Neendakara Harbor"


class SafetyCardSchema(BaseModel):
    status: SafetyStatus = SafetyStatus.SAFE
    label: str = "Safe"
    favorable_text: str = "Favorable"
    color_hex: str = "#16A34A"


class WeatherMetricsSchema(BaseModel):
    wind_kmh: float = 14.0
    wind_speed_knots: Optional[float] = 7.6
    wind_direction: Optional[str] = "West-Southwest"
    wave_m: float = 0.8
    rain: str = "Low"
    water_temp_c: float = 28.4
    risk_level: str = "low"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "IMD Coastal Radar / MOSDAC"


class OceanMetricsSchema(BaseModel):
    sea_surface_temperature_c: float = 28.4
    chlorophyll_density: str = "Favorable"
    chlorophyll_mg_m3: Optional[float] = 1.85
    ocean_current_knots: float = 0.4
    condition: str = "favorable"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "ISRO Oceansat-3"
    confidence: str = "high"


class BestZoneSchema(BaseModel):
    id: str = "A12"
    name: str = "Zone A-12"
    distance_km: float = 12.0
    direction: str = "Southwest"
    potential: PotentialLevel = PotentialLevel.HIGH
    course: int = 218
    depth_m: int = 44
    target_species: str = "Indian Mackerel & Sardines"
    est_run_time_min: int = 42


class RecommendationSchema(BaseModel):
    text: str = "Conditions are safe today. Recommended zone: 12 km southwest based on satellite chlorophyll and thermal current convergence."
    query_id: Optional[str] = None


class HomeStatusResponse(BaseModel):
    """
    Phase 51 Sample API Contract for Home Dashboard
    """
    location: LocationSchema
    connectivity: str = "online"
    data_mode: DataMode = DataMode.DEMO
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    safety: SafetyCardSchema
    weather: WeatherMetricsSchema
    ocean: OceanMetricsSchema
    best_zone: BestZoneSchema
    recommendation: RecommendationSchema
    active_alerts_count: int = 0


class AlertItem(BaseModel):
    id: str
    title: str
    severity: str  # 'danger' | 'caution' | 'info'
    area: str
    description: str
    valid_from: datetime
    valid_until: datetime
    source: str
    is_active: bool = True


class AlertsListResponse(BaseModel):
    alerts: List[AlertItem] = []
    has_active_alerts: bool = False
    status_summary: str = "All coastal sectors clear"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "INCOIS Marine Hazard Advisory"


class DataSourceStatus(BaseModel):
    source_name: str
    provider: str
    status: str  # 'verified' | 'cached' | 'offline' | 'demo'
    data_type: str
    last_sync: datetime
    quality_score: str = "High"


class DataStatusResponse(BaseModel):
    overall_mode: DataMode = DataMode.DEMO
    sources: List[DataSourceStatus]
    stale_threshold_hours: int = 6
    is_stale: bool = False
    message: str = "Data stream synchronized."
