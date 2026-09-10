import uuid
from datetime import datetime
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, String, Boolean, DateTime, Text
from backend.app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(16), default="info")  # danger | caution | info
    area = Column(String(128), default="Kollam Coast")
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime, default=datetime.utcnow)
    source = Column(String(64), default="INCOIS / IMD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
