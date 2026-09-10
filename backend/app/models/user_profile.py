from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, Boolean, DateTime
from backend.app.db.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String(64), primary_key=True, default="usr_ayub_01")
    name = Column(String(128), default="Ayub Chettiyar")
    vessel_name = Column(String(128), default="Sea King II")
    registration_no = Column(String(64), default="KL-02-F-491")
    preferred_language = Column(String(10), default="ml")
    latitude = Column(Float, default=8.88)
    longitude = Column(Float, default=76.59)
    location_name = Column(String(128), default="Kollam Coast")
    harbor = Column(String(128), default="Neendakara Harbor")
    avatar_url = Column(String(512), default="")
    voice_enabled = Column(Boolean, default=True)
    notifications_enabled = Column(Boolean, default=True)
    gps_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
