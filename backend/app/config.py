import os
from pathlib import Path
from typing import List, Optional
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "ORCA Marine Telemetry & AI Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    DEMO_MODE: bool = True
    DEMO_FALLBACK: bool = True
    PRESENTATION_MODE: bool = True

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

    # LLM Settings (Google Gemini) - API key strictly loaded from environment
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GEMINI_TEXT_MODEL: str = "gemini-3.6-flash"
    MODEL_NAME: str = "gemini-3.6-flash"

    # Google Maps Platform (Browser key for frontend map visualization)
    GOOGLE_MAPS_BROWSER_KEY: str = ""
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

    # Pluggable Speech Settings (Groq Whisper & Fish Audio)
    STT_PROVIDER: str = "groq"
    STT_API_KEY: str = ""
    STT_MODEL: str = "whisper-large-v3-turbo"

    TTS_PROVIDER: str = "fish_audio"
    FISH_AUDIO_API_KEY: str = ""
    TTS_API_KEY: str = ""
    FISH_AUDIO_MODEL: str = "s2.1-pro-free"
    TTS_MODEL: str = "s2.1-pro-free"
    FISH_AUDIO_VOICE_ID: Optional[str] = None
    FISH_AUDIO_VOICE_ID_EN: Optional[str] = None
    FISH_AUDIO_VOICE_ID_TA: Optional[str] = None
    FISH_AUDIO_VOICE_ID_ML: Optional[str] = None

    # Default Reference Location (Kollam Coast)
    DEFAULT_LOCATION_NAME: str = "Kollam Coast"
    DEFAULT_LATITUDE: float = 8.88
    DEFAULT_LONGITUDE: float = 76.59
    DEFAULT_HARBOR: str = "Neendakara Harbor"

    # RAG & Local Intelligence Settings
    RAG_ENABLED: bool = True
    RAG_INDEX_DIR: str = "backend/rag/index"
    RAG_MODEL_DIR: str = "backend/rag/models"
    RAG_TOP_K: int = 5

    model_config = SettingsConfigDict(
        env_file=[
            Path(__file__).resolve().parents[2] / ".env",
            Path(__file__).resolve().parents[1] / ".env",
        ],
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )

    def get_effective_gemini_model(self) -> str:
        return self.GEMINI_TEXT_MODEL or self.MODEL_NAME or "gemini-3.6-flash"

    def get_effective_maps_key(self) -> str:
        return self.GOOGLE_MAPS_BROWSER_KEY or self.GOOGLE_MAPS_KEY or ""

    def get_effective_tts_key(self) -> str:
        return self.FISH_AUDIO_API_KEY or self.TTS_API_KEY or ""

    def get_effective_tts_model(self) -> str:
        return self.FISH_AUDIO_MODEL or self.TTS_MODEL or "s2.1-pro-free"


settings = Settings()
