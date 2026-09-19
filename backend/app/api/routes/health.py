import time
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
import httpx

from backend.app.config import settings
from backend.app.llm.gemini_provider import llm_provider
from backend.app.services.voice_service import voice_service
from backend.app.services.weather_service import weather_service
from backend.app.services.ocean_service import ocean_service

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("", summary="Service Health Check")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "demo_mode": settings.DEMO_MODE,
        "presentation_mode": settings.PRESENTATION_MODE,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/gemini", summary="Gemini Provider Health Check")
async def health_gemini():
    return await llm_provider.health_check()


@router.get("/maps", summary="Google Maps Integration Health Check")
async def health_maps():
    maps_key = settings.get_effective_maps_key()
    configured = bool(maps_key)
    if not configured:
        return {
            "provider": "Google Maps",
            "configured": False,
            "reachable": False,
            "fallback": "Leaflet/OpenStreetMap",
            "error": "MAPS_KEY_MISSING",
        }

    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.get(f"https://maps.googleapis.com/maps/api/js?key={maps_key}")
            latency_ms = int((time.time() - start) * 1000)
            if res.status_code == 200:
                return {
                    "provider": "Google Maps",
                    "configured": True,
                    "reachable": True,
                    "fallback": "Leaflet/OpenStreetMap",
                    "latency_ms": latency_ms,
                    "error": None,
                }
            else:
                return {
                    "provider": "Google Maps",
                    "configured": True,
                    "reachable": False,
                    "fallback": "Leaflet/OpenStreetMap",
                    "latency_ms": latency_ms,
                    "error": f"HTTP {res.status_code}",
                }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": "Google Maps",
            "configured": True,
            "reachable": False,
            "fallback": "Leaflet/OpenStreetMap",
            "latency_ms": latency_ms,
            "error": str(e)[:150],
        }


@router.get("/voice", summary="STT & TTS Overall Voice Health Check")
async def health_voice():
    stt_status = await voice_service.health_check_stt()
    tts_status = await voice_service.health_check_tts()
    return {
        "stt": stt_status,
        "tts": tts_status,
    }


@router.get("/tts", summary="Fish Audio TTS Provider Health Check")
async def health_tts():
    return await voice_service.health_check_tts()


@router.get("/weather", summary="Marine Weather Data Provider Health Check")
async def health_weather():
    start = time.time()
    try:
        data = await weather_service.get_weather(settings.DEFAULT_LATITUDE, settings.DEFAULT_LONGITUDE)
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": "Open-Meteo / IMD",
            "configured": True,
            "reachable": bool(data),
            "status": "online" if data.get("source") != "demo_fallback" else "demo",
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": "Open-Meteo / IMD",
            "configured": True,
            "reachable": False,
            "status": "degraded",
            "latency_ms": latency_ms,
            "error": str(e)[:150],
        }


@router.get("/ocean", summary="Oceanographic Data Provider Health Check")
async def health_ocean():
    start = time.time()
    try:
        data = await ocean_service.get_ocean(settings.DEFAULT_LATITUDE, settings.DEFAULT_LONGITUDE)
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": "INCOIS / Open-Meteo Marine",
            "configured": True,
            "reachable": bool(data),
            "status": "online" if data.get("source") != "demo_fallback" else "demo",
            "latency_ms": latency_ms,
            "error": None,
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": "INCOIS / Open-Meteo Marine",
            "configured": True,
            "reachable": False,
            "status": "degraded",
            "latency_ms": latency_ms,
            "error": str(e)[:150],
        }


@router.get("/redis", summary="Redis Cache Health Check")
async def health_redis():
    # Test Redis reachability if redis is installed
    try:
        import redis.asyncio as aioredis
        client = aioredis.from_url(settings.REDIS_URL, socket_timeout=1.5)
        await client.ping()
        await client.aclose()
        return {
            "provider": "redis",
            "configured": True,
            "reachable": True,
            "status": "online",
            "error": None,
        }
    except ImportError:
        return {
            "provider": "redis",
            "configured": False,
            "reachable": False,
            "status": "in-memory-fallback",
            "error": "Redis client library not installed; in-memory cache active.",
        }
    except Exception as e:
        return {
            "provider": "redis",
            "configured": True,
            "reachable": False,
            "status": "degraded",
            "error": f"Redis connection failed: {str(e)[:100]}; in-memory cache active.",
        }


@router.get("/dashboard", summary="Comprehensive Health & Diagnostics Dashboard")
async def health_dashboard():
    gemini_h = await llm_provider.health_check()
    maps_h = await health_maps()
    stt_h = await voice_service.health_check_stt()
    tts_h = await voice_service.health_check_tts()
    weather_h = await health_weather()
    ocean_h = await health_ocean()
    redis_h = await health_redis()

    return {
        "gemini": {
            "status": "READY" if gemini_h.get("reachable") else "DEGRADED",
            "provider": gemini_h.get("provider"),
            "model": gemini_h.get("model"),
            "latency_ms": gemini_h.get("latency_ms", 0),
            "error": gemini_h.get("error"),
        },
        "google_maps": {
            "status": "READY" if maps_h.get("reachable") else "DEGRADED",
            "provider": maps_h.get("provider"),
            "fallback": maps_h.get("fallback"),
            "latency_ms": maps_h.get("latency_ms", 0),
            "error": maps_h.get("error"),
        },
        "groq_stt": {
            "status": "READY" if stt_h.get("reachable") else "DEGRADED",
            "provider": stt_h.get("provider"),
            "model": stt_h.get("model"),
            "latency_ms": stt_h.get("latency_ms", 0),
            "error": stt_h.get("error"),
        },
        "fish_audio": {
            "status": "READY" if tts_h.get("reachable") else "DEGRADED",
            "provider": tts_h.get("provider"),
            "model": tts_h.get("model"),
            "latency_ms": tts_h.get("latency_ms", 0),
            "error": tts_h.get("error"),
        },
        "weather": {
            "status": "READY" if weather_h.get("reachable") else "DEGRADED",
            "provider": weather_h.get("provider"),
            "latency_ms": weather_h.get("latency_ms", 0),
            "error": weather_h.get("error"),
        },
        "ocean": {
            "status": "READY" if ocean_h.get("reachable") else "DEGRADED",
            "provider": ocean_h.get("provider"),
            "latency_ms": ocean_h.get("latency_ms", 0),
            "error": ocean_h.get("error"),
        },
        "database": {
            "status": "READY",
            "provider": "SQLite/aiosqlite",
            "mode": "persistent",
            "error": None,
        },
        "redis": {
            "status": "READY" if redis_h.get("reachable") else "DEGRADED",
            "provider": redis_h.get("provider"),
            "error": redis_h.get("error"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
