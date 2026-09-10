import uuid
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, DateTime, Text
from backend.app.db.base import Base


class OrcaRecommendation(Base):
    __tablename__ = "orca_recommendations"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    query_id = Column(String(64), nullable=True, index=True)
    safety_status = Column(String(16), default="safe")
    recommended_zone_id = Column(String(32), default="A12")
    response_text = Column(Text, nullable=False)
    weather_result = Column(Text, nullable=True)  # JSON serialized
    ocean_result = Column(Text, nullable=True)    # JSON serialized
    fishing_zone_result = Column(Text, nullable=True)  # JSON serialized
    safety_result = Column(Text, nullable=True)   # JSON serialized
    confidence = Column(Float, default=0.98)
    generated_at = Column(DateTime, default=datetime.utcnow)
