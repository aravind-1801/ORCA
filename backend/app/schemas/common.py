from enum import Enum
from typing import Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class SafetyStatus(str, Enum):
    SAFE = "safe"
    CAUTION = "caution"
    DANGER = "danger"


class PotentialLevel(str, Enum):
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class DataMode(str, Enum):
    LIVE = "live"
    CACHED = "cached"
    DEMO = "demo"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Standardized error code")
    message: str = Field(..., description="User-friendly error message")
    details: Optional[Any] = None


class APIErrorResponse(BaseModel):
    error: ErrorDetail
