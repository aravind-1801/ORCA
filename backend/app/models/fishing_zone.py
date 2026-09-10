import uuid
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from backend.app.db.base import Base


class FishingZone(Base):
    __tablename__ = "fishing_zones"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    code = Column(String(32), index=True)
    name = Column(String(64))
    centroid_latitude = Column(Float, nullable=False)
    centroid_longitude = Column(Float, nullable=False)
    distance_km = Column(Float, nullable=False)
    direction = Column(String(32), nullable=False)
    course_deg = Column(Integer, default=218)
    depth_m = Column(Integer, default=44)
    potential_level = Column(String(16), default="high")  # high | moderate | low
    confidence = Column(Float, default=0.92)
    source = Column(String(64), default="INCOIS PFZ")
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text, nullable=True)
    data_mode = Column(String(16), default="demo")
    created_at = Column(DateTime, default=datetime.utcnow)
