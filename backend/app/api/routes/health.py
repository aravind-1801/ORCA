from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", summary="Service Health Check")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
