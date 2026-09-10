import uuid
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Float, DateTime, Text
from backend.app.db.base import Base


class OrcaQuery(Base):
    __tablename__ = "orca_queries"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), default="usr_ayub_01")
    query_text = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
