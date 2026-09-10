from datetime import datetime
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from backend.app.schemas.common import PotentialLevel, DataMode


class EnvironmentalDiagnostics(BaseModel):
    sea_surface_temp_c: float = 28.4
    chlorophyll_density: str = "High plankton concentration"
    surface_wind_kmh: float = 14.0
    wave_height_m: float = 0.8
    bottom_depth_m: int = 44


class FishingZoneItem(BaseModel):
    id: str = "A12"
    code: str = "ZONE A-12"
    name: str = "Zone A-12"
    latitude: float = 8.78
    longitude: float = 76.49
    distance_km: float = 12.0
    direction: str = "Southwest"
    course_deg: int = 218
    course_heading: str = "218° SSW"
    bottom_depth_m: int = 44
    potential: PotentialLevel = PotentialLevel.HIGH
    confidence: str = "high"
    source: str = "INCOIS PFZ-7 / Oceansat-3"
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime = Field(default_factory=datetime.utcnow)
    target_species: List[str] = ["Indian Mackerel", "Oil Sardine", "Skipjack Tuna"]
    diagnostics: Optional[EnvironmentalDiagnostics] = None
    data_mode: DataMode = DataMode.DEMO


class FishingZonesListResponse(BaseModel):
    zones: List[FishingZoneItem]
    vessel_location: dict = {
        "name": "Sea King II",
        "latitude": 8.88,
        "longitude": 76.59,
        "status": "GPS Fixed"
    }
    recommended_zone_id: str = "A12"
    data_mode: DataMode = DataMode.DEMO
    updated_at: datetime = Field(default_factory=datetime.utcnow)
