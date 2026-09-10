from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from backend.app.config import settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.user_profile import UserProfile
from backend.app.utils.logging import logger

router = APIRouter(prefix="/location", tags=["Location"])


class LocationSchema(BaseModel):
    location_name: str = "Kollam Coast"
    harbor: str = "Neendakara Harbor"
    latitude: float = 8.88
    longitude: float = 76.59
    state: str = "Kerala"
    country: str = "India"
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LocationUpdate(BaseModel):
    location_name: Optional[str] = None
    harbor: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    state: Optional[str] = None


# Active runtime location state
_ACTIVE_LOCATION = LocationSchema(
    location_name=settings.DEFAULT_LOCATION_NAME,
    harbor=settings.DEFAULT_HARBOR,
    latitude=settings.DEFAULT_LATITUDE,
    longitude=settings.DEFAULT_LONGITUDE,
    state="Kerala",
    country="India",
)


def get_current_location() -> LocationSchema:
    return _ACTIVE_LOCATION


@router.get("", response_model=LocationSchema, summary="Get current active location")
async def get_location():
    return _ACTIVE_LOCATION


@router.put("", response_model=LocationSchema, summary="Update active location")
async def update_location(payload: LocationUpdate):
    global _ACTIVE_LOCATION
    current_data = _ACTIVE_LOCATION.model_dump()
    updates = payload.model_dump(exclude_unset=True)
    current_data.update(updates)
    current_data["updated_at"] = datetime.now(timezone.utc)
    _ACTIVE_LOCATION = LocationSchema(**current_data)

    # Synchronize with UserProfile in DB and memory
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserProfile).where(UserProfile.id == "usr_ayub_01")
            res = await session.execute(stmt)
            profile = res.scalar_one_or_none()
            if profile:
                if payload.location_name:
                    profile.location_name = payload.location_name
                if payload.harbor:
                    profile.harbor = payload.harbor
                if payload.latitude is not None:
                    profile.latitude = payload.latitude
                if payload.longitude is not None:
                    profile.longitude = payload.longitude
                profile.updated_at = datetime.now(timezone.utc)
                await session.commit()
    except Exception as e:
        logger.warning(f"Error persisting location to UserProfile in DB: {e}")

    logger.info(f"Updated global location to {_ACTIVE_LOCATION.location_name} ({_ACTIVE_LOCATION.latitude}, {_ACTIVE_LOCATION.longitude})")
    return _ACTIVE_LOCATION


@router.post("/current", response_model=LocationSchema, summary="Set location from device GPS")
async def set_current_gps_location(payload: LocationUpdate):
    return await update_location(payload)
