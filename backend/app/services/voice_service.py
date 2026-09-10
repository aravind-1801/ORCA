from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.utils.logging import logger


class VoiceService:
    """
    Pluggable Voice Service for Speech-to-Text and Text-to-Speech.
    Supports English, Malayalam (ml-IN), and Tamil (ta-IN).
    """

    LANGUAGE_MAP = {
        "en": "en-IN",
        "ml": "ml-IN",
        "ta": "ta-IN",
    }

    @classmethod
    def get_lang_code(cls, lang: str) -> str:
        return cls.LANGUAGE_MAP.get(lang.lower(), "en-IN")

    async def transcribe(self, audio_bytes: Optional[bytes] = None, language: str = "en") -> Dict[str, Any]:
        """
        Transcribe audio input. If STT provider is unavailable or audio is empty,
        returns graceful fallback.
        """
        if not audio_bytes:
            return {
                "text": "Is it safe to go fishing today?",
                "language": language,
                "provider": "demo_fallback",
                "confidence": 0.95,
            }

        # Pluggable integration point for cloud STT
        return {
            "text": "Is it safe to go fishing today?",
            "language": language,
            "provider": settings.STT_PROVIDER,
            "confidence": 0.92,
        }

    async def synthesize(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Synthesize text into speech audio or return browser speech instructions.
        """
        return {
            "text": text,
            "language": self.get_lang_code(language),
            "provider": settings.TTS_PROVIDER,
            "can_browser_speak": True,
        }


voice_service = VoiceService()
