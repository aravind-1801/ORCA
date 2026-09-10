from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from sqlalchemy import select
from backend.app.schemas.profile import UserProfileSchema, UserProfileUpdate
from backend.app.models.user_profile import UserProfile
from backend.app.db.session import AsyncSessionLocal
from backend.app.api.routes.location import _ACTIVE_LOCATION, LocationSchema
from backend.app.utils.logging import logger

router = APIRouter(prefix="/profile", tags=["User Profile"])

# In-memory working state
_CURRENT_PROFILE = UserProfileSchema(
    id="usr_ayub_01",
    name="Ayub Chettiyar",
    vessel_name="Sea King II",
    registration_no="KL-02-F-491",
    vessel_type="Motorized Craft (28ft)",
    preferred_language="ml",
    base_port="Kollam, KL",
    harbor="Neendakara Harbor",
    location_name="Kollam Coast",
    avatar_url="",
    latitude=8.88,
    longitude=76.59,
    gps_enabled=True,
    voice_enabled=True,
    notifications_enabled=True,
)


class ProfileImagePayload(BaseModel):
    image: Optional[str] = None
    avatar_url: Optional[str] = None


@router.get("", response_model=UserProfileSchema, summary="Get current fisherman profile")
async def get_profile():
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserProfile).where(UserProfile.id == _CURRENT_PROFILE.id)
            res = await session.execute(stmt)
            db_profile = res.scalar_one_or_none()
            if db_profile:
                return UserProfileSchema(
                    id=db_profile.id,
                    name=db_profile.name or _CURRENT_PROFILE.name,
                    vessel_name=db_profile.vessel_name or _CURRENT_PROFILE.vessel_name,
                    registration_no=db_profile.registration_no or _CURRENT_PROFILE.registration_no,
                    vessel_type=_CURRENT_PROFILE.vessel_type,
                    preferred_language=db_profile.preferred_language or _CURRENT_PROFILE.preferred_language,
                    base_port=_CURRENT_PROFILE.base_port,
                    harbor=db_profile.harbor or _CURRENT_PROFILE.harbor,
                    location_name=db_profile.location_name or _CURRENT_PROFILE.location_name,
                    avatar_url=db_profile.avatar_url or "",
                    latitude=db_profile.latitude or _CURRENT_PROFILE.latitude,
                    longitude=db_profile.longitude or _CURRENT_PROFILE.longitude,
                    gps_enabled=db_profile.gps_enabled if db_profile.gps_enabled is not None else True,
                    voice_enabled=db_profile.voice_enabled if db_profile.voice_enabled is not None else True,
                    notifications_enabled=db_profile.notifications_enabled if db_profile.notifications_enabled is not None else True,
                )
    except Exception as e:
        logger.warning(f"DB load for profile failed ({e}). Returning memory state.")

    return _CURRENT_PROFILE


@router.put("", response_model=UserProfileSchema, summary="Replace fisherman profile")
@router.patch("", response_model=UserProfileSchema, summary="Update fisherman profile and preferences")
async def update_profile(updates: UserProfileUpdate):
    global _CURRENT_PROFILE
    current_data = _CURRENT_PROFILE.model_dump()
    update_data = updates.model_dump(exclude_unset=True)
    current_data.update(update_data)
    current_data["updated_at"] = datetime.now(timezone.utc)
    _CURRENT_PROFILE = UserProfileSchema(**current_data)

    # Sync with global active location if location changed
    if updates.location_name or updates.latitude is not None or updates.longitude is not None:
        if updates.location_name:
            _ACTIVE_LOCATION.location_name = updates.location_name
        if updates.harbor:
            _ACTIVE_LOCATION.harbor = updates.harbor
        if updates.latitude is not None:
            _ACTIVE_LOCATION.latitude = updates.latitude
        if updates.longitude is not None:
            _ACTIVE_LOCATION.longitude = updates.longitude

    # Persist to database
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserProfile).where(UserProfile.id == _CURRENT_PROFILE.id)
            res = await session.execute(stmt)
            db_profile = res.scalar_one_or_none()
            if not db_profile:
                db_profile = UserProfile(id=_CURRENT_PROFILE.id)
                session.add(db_profile)

            for field, val in update_data.items():
                if hasattr(db_profile, field) and val is not None:
                    setattr(db_profile, field, val)

            db_profile.updated_at = datetime.now(timezone.utc)
            await session.commit()
    except Exception as e:
        logger.warning(f"DB persist for profile failed ({e}).")

    logger.info(f"Profile updated successfully: {_CURRENT_PROFILE.name} ({_CURRENT_PROFILE.location_name})")
    return _CURRENT_PROFILE


@router.post("/image", summary="Upload or update profile avatar image")
async def upload_profile_image(payload: ProfileImagePayload):
    global _CURRENT_PROFILE
    img_data = payload.avatar_url or payload.image or ""
    _CURRENT_PROFILE.avatar_url = img_data

    # Persist to DB
    try:
        async with AsyncSessionLocal() as session:
            stmt = select(UserProfile).where(UserProfile.id == _CURRENT_PROFILE.id)
            res = await session.execute(stmt)
            db_profile = res.scalar_one_or_none()
            if db_profile:
                db_profile.avatar_url = img_data
                await session.commit()
    except Exception as e:
        logger.warning(f"Failed to persist avatar_url to DB: {e}")

    return {
        "status": "success",
        "message": "Profile image updated successfully",
        "avatar_url": img_data,
    }
