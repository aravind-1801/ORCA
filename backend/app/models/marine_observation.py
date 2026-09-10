import uuid
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, DateTime
from backend.app.db.base import Base


class MarineObservation(Base):
    __tablename__ = "marine_observations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    sea_surface_temperature = Column(Float, nullable=True)
    chlorophyll = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)  # km/h
    wave_height = Column(Float, nullable=True)  # meters
    rainfall = Column(String(32), default="Low")
    ocean_current = Column(Float, default=0.4)  # knots
    source = Column(String(64), default="ISRO / MOSDAC / IMD")
    confidence = Column(Float, default=0.95)
    data_mode = Column(String(16), default="demo")
    created_at = Column(DateTime, default=datetime.utcnow)
