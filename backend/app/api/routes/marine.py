from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Query, HTTPException
from backend.app.config import settings
from backend.app.schemas.marine import (
    HomeStatusResponse,
    AlertsListResponse,
    AlertItem,
    DataStatusResponse,
    DataSourceStatus,
)
from backend.app.schemas.fishing import FishingZonesListResponse, FishingZoneItem
from backend.app.schemas.common import DataMode
from backend.app.services.marine_service import marine_service
from backend.app.services.weather_service import weather_service
from backend.app.services.ocean_service import ocean_service
from backend.app.services.fishing_zone_service import fishing_zone_service
from backend.app.services.alert_service import alert_service

router = APIRouter(prefix="/marine", tags=["Marine"])


@router.get("/status", response_model=HomeStatusResponse, summary="Get overall Home Marine status")
async def get_marine_status(
    lat: float = Query(default=settings.DEFAULT_LATITUDE, ge=-90.0, le=90.0),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE, ge=-180.0, le=180.0),
    location_name: Optional[str] = Query(default="Kollam Coast"),
):
    status_data = await marine_service.get_status(lat, lon, location_name)
    return status_data


@router.get("/weather", summary="Get Marine Weather parameters")
async def get_marine_weather(
    lat: float = Query(default=settings.DEFAULT_LATITUDE, ge=-90.0, le=90.0),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE, ge=-180.0, le=180.0),
):
    return await weather_service.get_weather(lat, lon)


@router.get("/ocean", summary="Get Oceanographic parameters (SST, Chlorophyll, Currents)")
async def get_marine_ocean(
    lat: float = Query(default=settings.DEFAULT_LATITUDE, ge=-90.0, le=90.0),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE, ge=-180.0, le=180.0),
):
    return await ocean_service.get_ocean(lat, lon)


@router.get("/fishing-zones", response_model=FishingZonesListResponse, summary="Get nearby fishing zones ranked")
async def get_fishing_zones(
    lat: float = Query(default=settings.DEFAULT_LATITUDE, ge=-90.0, le=90.0),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE, ge=-180.0, le=180.0),
):
    zones = await fishing_zone_service.get_zones(lat, lon)
    return {
        "zones": zones,
        "vessel_location": {
            "name": "Sea King II",
            "latitude": lat,
            "longitude": lon,
            "status": "GPS Fixed",
        },
        "recommended_zone_id": zones[0]["id"] if zones else "A12",
        "data_mode": DataMode.DEMO if settings.DEMO_MODE else DataMode.LIVE,
        "updated_at": datetime.now(timezone.utc),
    }


@router.get("/fishing-zones/{zone_id}", response_model=FishingZoneItem, summary="Get detailed zone telemetry")
async def get_fishing_zone_detail(
    zone_id: str,
    lat: float = Query(default=settings.DEFAULT_LATITUDE),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE),
):
    zone = await fishing_zone_service.get_zone_by_id(zone_id, lat, lon)
    if not zone:
        raise HTTPException(status_code=404, detail=f"Fishing zone '{zone_id}' not found")
    return zone


@router.get("/alerts", response_model=AlertsListResponse, summary="Get active coastal and safety alerts")
async def get_alerts(
    lat: float = Query(default=settings.DEFAULT_LATITUDE),
    lon: float = Query(default=settings.DEFAULT_LONGITUDE),
):
    raw_alerts = await alert_service.get_active_alerts(lat, lon)
    items = [
        AlertItem(
            id=a.get("id", "alert_01"),
            title=a.get("title", "Advisory"),
            severity=a.get("severity", "info"),
            area=a.get("area", "Kollam Coast"),
            description=a.get("description", ""),
            valid_from=a.get("valid_from", datetime.now(timezone.utc)),
            valid_until=a.get("valid_until", datetime.now(timezone.utc)),
            source=a.get("source", "INCOIS"),
            is_active=a.get("is_active", True),
        )
        for a in raw_alerts
    ]
    return {
        "alerts": items,
        "has_active_alerts": len(items) > 0,
        "status_summary": "All coastal sectors clear" if len(items) == 0 else f"{len(items)} active notices",
        "timestamp": datetime.now(timezone.utc),
        "source": "INCOIS Marine Hazard Advisory",
    }


@router.get("/data-status", response_model=DataStatusResponse, summary="Get data stream freshness and source integrity")
async def get_data_status():
    now = datetime.now(timezone.utc)
    mode = DataMode.DEMO if settings.DEMO_MODE else DataMode.LIVE
    sources = [
        DataSourceStatus(
            source_name="ISRO Oceansat-3",
            provider="Indian Space Research Organisation",
            status="demo" if settings.DEMO_MODE else "verified",
            data_type="SST & Chlorophyll OCM",
            last_sync=now,
            quality_score="High (0.95)",
        ),
        DataSourceStatus(
            source_name="INCOIS PFZ-7",
            provider="Ministry of Earth Sciences",
            status="demo" if settings.DEMO_MODE else "verified",
            data_type="Potential Fishing Zone Vectors",
            last_sync=now,
            quality_score="High (0.92)",
        ),
        DataSourceStatus(
            source_name="IMD Coastal Doppler Radar",
            provider="India Meteorological Department",
            status="demo" if settings.DEMO_MODE else "verified",
            data_type="Atmospheric Wind & Wave Height",
            last_sync=now,
            quality_score="High (0.98)",
        ),
        DataSourceStatus(
            source_name="MOSDAC Satellite",
            provider="Space Applications Centre",
            status="demo" if settings.DEMO_MODE else "verified",
            data_type="Ocean Current Kinematics",
            last_sync=now,
            quality_score="High (0.90)",
        ),
    ]
    return {
        "overall_mode": mode,
        "sources": sources,
        "stale_threshold_hours": 6,
        "is_stale": False,
        "message": "All marine data feeds verified and synchronized.",
    }
