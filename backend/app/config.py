import os
from typing import List
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ORCA Marine Telemetry & AI Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
    ]

    # Database
    # Default to local SQLite fallback if PostgreSQL is not specified/reachable
    DATABASE_URL: str = "sqlite+aiosqlite:///./orca_marine.db"
    SYNC_DATABASE_URL: str = "sqlite:///./orca_marine.db"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_DEFAULT_TTL_SEC: int = 300  # 5 minutes
    CACHE_ALERT_TTL_SEC: int = 120    # 2 minutes for alerts

    # LLM Settings
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    MODEL_NAME: str = "gemini-3.6-flash"

    # Google Maps Platform (served to frontend via /api/v1/config — never exposed in source)
    GOOGLE_MAPS_KEY: str = ""

    # Safety Rule Engine Thresholds
    SAFETY_WAVE_CAUTION_M: float = 1.5
    SAFETY_WAVE_DANGER_M: float = 2.5
    SAFETY_WIND_CAUTION_KMH: float = 25.0
    SAFETY_WIND_DANGER_KMH: float = 40.0
    SAFETY_SWELL_CAUTION_M: float = 1.8
    SAFETY_SWELL_DANGER_M: float = 2.8

    # External Data Sources
    ISRO_BASE_URL: str = "https://mosdac.gov.in/api/v1"
    MOSDAC_BASE_URL: str = "https://mosdac.gov.in/api/v1"
    INCOIS_BASE_URL: str = "https://incois.gov.in/api/v1"
    WEATHER_API_BASE_URL: str = "https://api.open-meteo.com/v1"

    # Pluggable Speech Settings
    STT_PROVIDER: str = "browser"  # 'browser' | 'gemini' | 'mock'
    STT_API_KEY: str = ""
    TTS_PROVIDER: str = "browser"  # 'browser' | 'google' | 'mock'
    TTS_API_KEY: str = ""

    # Default Reference Location (Kollam Coast)
    DEFAULT_LOCATION_NAME: str = "Kollam Coast"
    DEFAULT_LATITUDE: float = 8.88
    DEFAULT_LONGITUDE: float = 76.59
    DEFAULT_HARBOR: str = "Neendakara Harbor"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
