from datetime import datetime
from typing import Optional
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class UserProfileSchema(BaseModel):
    id: str = "usr_ayub_01"
    name: str = "Ayub Chettiyar"
    vessel_name: str = "Sea King II"
    registration_no: str = "KL-02-F-491"
    vessel_type: str = "Motorized Craft (28ft)"
    preferred_language: str = "ml"  # 'ml' | 'en' | 'ta'
    base_port: str = "Kollam, KL"
    harbor: str = "Neendakara Harbor"
    location_name: str = "Kollam Coast"
    avatar_url: str = ""
    latitude: float = 8.88
    longitude: float = 76.59
    gps_enabled: bool = True
    voice_enabled: bool = True
    notifications_enabled: bool = True
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    vessel_name: Optional[str] = None
    registration_no: Optional[str] = None
    vessel_type: Optional[str] = None
    preferred_language: Optional[str] = None
    base_port: Optional[str] = None
    harbor: Optional[str] = None
    location_name: Optional[str] = None
    avatar_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gps_enabled: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
