import base64
import json
import time
from typing import Dict, Any, Optional
import httpx

from backend.app.config import settings
from backend.app.utils.logging import logger


class VoiceService:
    """
    Pluggable Voice Service for Speech-to-Text (Groq Whisper)
    and Text-to-Speech (Fish Audio).
    Strictly follows modern provider contracts, validates binary outputs,
    and returns predictable schemas without swallowing errors.
    """

    LANGUAGE_MAP = {
        "en": "en",
        "ml": "ml",
        "ta": "ta",
        "en-in": "en",
        "ml-in": "ml",
        "ta-in": "ta",
    }

    @classmethod
    def normalize_lang(cls, lang: str) -> str:
        if not lang:
            return "en"
        l = lang.lower().strip()
        if l.startswith("ta"):
            return "ta"
        if l.startswith("ml"):
            return "ml"
        return "en"

    async def transcribe(
        self,
        audio_bytes: Optional[bytes] = None,
        language: str = "en",
        filename: str = "audio.webm",
        content_type: str = "audio/webm",
    ) -> Dict[str, Any]:
        """
        Transcribe audio input via Groq Whisper API.
        Respects actual MIME types (webm, ogg, mp4, wav).
        """
        norm_lang = self.normalize_lang(language)

        if not audio_bytes or len(audio_bytes) < 64:
            return {
                "success": False,
                "text": "",
                "language": norm_lang,
                "provider": settings.STT_PROVIDER or "groq",
                "model": settings.STT_MODEL,
                "error": {
                    "code": "EMPTY_AUDIO",
                    "message": "Audio payload was empty or too short to transcribe.",
                },
            }

        provider = (settings.STT_PROVIDER or "groq").lower()
        if provider == "groq" and settings.STT_API_KEY:
            try:
                # Ensure correct file extension matching MIME type
                ext = "webm"
                if "ogg" in content_type:
                    ext = "ogg"
                elif "mp4" in content_type or "m4a" in content_type:
                    ext = "mp4"
                elif "wav" in content_type:
                    ext = "wav"
                elif "mp3" in content_type or "mpeg" in content_type:
                    ext = "mp3"

                upload_filename = f"audio.{ext}"

                async with httpx.AsyncClient(timeout=30.0) as client:
                    files = {
                        "file": (upload_filename, audio_bytes, content_type),
                    }
                    data = {
                        "model": settings.STT_MODEL,
                        "response_format": "json",
                        "language": norm_lang,
                    }
                    headers = {
                        "Authorization": f"Bearer {settings.STT_API_KEY}",
                    }
                    res = await client.post(
                        "https://api.groq.com/openai/v1/audio/transcriptions",
                        headers=headers,
                        files=files,
                        data=data,
                    )
                    if res.status_code == 200:
                        payload = res.json()
                        text = str(payload.get("text") or "").strip()
                        return {
                            "success": True,
                            "text": text,
                            "language": norm_lang,
                            "provider": "groq",
                            "model": settings.STT_MODEL,
                            "error": None,
                        }
                    else:
                        err_text = res.text[:200]
                        logger.warning(f"Groq STT returned HTTP {res.status_code}: {err_text}")
                        return {
                            "success": False,
                            "text": "",
                            "language": norm_lang,
                            "provider": "groq",
                            "model": settings.STT_MODEL,
                            "error": {
                                "code": f"HTTP_{res.status_code}",
                                "message": f"Groq STT transcription failed: {err_text}",
                            },
                        }
            except Exception as exc:
                logger.error(f"Groq STT transcription exception: {exc}")
                return {
                    "success": False,
                    "text": "",
                    "language": norm_lang,
                    "provider": "groq",
                    "model": settings.STT_MODEL,
                    "error": {
                        "code": "STT_NETWORK_ERROR",
                        "message": str(exc),
                    },
                }

        # Fallback for presentation when no cloud key is configured
        return {
            "success": False,
            "text": "",
            "language": norm_lang,
            "provider": provider,
            "model": settings.STT_MODEL,
            "error": {
                "code": "STT_NOT_CONFIGURED",
                "message": "Groq STT API key is not configured.",
            },
        }

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize text into speech audio using Fish Audio (/v1/tts).
        Validates content-type and binary output, returning base64 MP3.
        """
        norm_lang = self.normalize_lang(language)
        provider = (settings.TTS_PROVIDER or "fish_audio").lower()
        api_key = settings.get_effective_tts_key()
        model = settings.get_effective_tts_model()

        if not text or not text.strip():
            return {
                "success": False,
                "provider": provider,
                "audio_base64": None,
                "audio_format": "mp3",
                "language": norm_lang,
                "voice_id": voice_id,
                "error": {
                    "code": "EMPTY_TEXT",
                    "message": "Text for speech synthesis cannot be empty.",
                },
            }

        if provider == "fish_audio" and api_key:
            try:
                # Select voice ID based on language if configured
                effective_voice = voice_id
                if not effective_voice:
                    if norm_lang == "ta":
                        effective_voice = settings.FISH_AUDIO_VOICE_ID_TA or settings.FISH_AUDIO_VOICE_ID
                    elif norm_lang == "ml":
                        effective_voice = settings.FISH_AUDIO_VOICE_ID_ML or settings.FISH_AUDIO_VOICE_ID
                    else:
                        effective_voice = settings.FISH_AUDIO_VOICE_ID_EN or settings.FISH_AUDIO_VOICE_ID

                async with httpx.AsyncClient(timeout=30.0) as client:
                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "model": model,
                    }
                    payload: Dict[str, Any] = {
                        "text": text,
                        "format": "mp3",
                    }
                    if effective_voice:
                        payload["reference_id"] = effective_voice

                    res = await client.post(
                        "https://api.fish.audio/v1/tts",
                        headers=headers,
                        json=payload,
                    )

                    if res.status_code == 200:
                        content_type = res.headers.get("content-type", "").lower()
                        # Validate binary audio returned
                        if ("audio" in content_type or "mpeg" in content_type or "mp3" in content_type or "octet-stream" in content_type) and len(res.content) > 100:
                            audio_b64 = base64.b64encode(res.content).decode("ascii")
                            return {
                                "success": True,
                                "provider": "fish_audio",
                                "audio_base64": audio_b64,
                                "audio_format": "mp3",
                                "language": norm_lang,
                                "voice_id": effective_voice,
                                "error": None,
                            }
                        else:
                            # Response is not valid audio (may be an encoded error JSON)
                            try:
                                error_json = res.json()
                            except Exception:
                                error_json = res.text[:200]
                            return {
                                "success": False,
                                "provider": "fish_audio",
                                "audio_base64": None,
                                "audio_format": "mp3",
                                "language": norm_lang,
                                "voice_id": effective_voice,
                                "error": {
                                    "code": "INVALID_AUDIO_STREAM",
                                    "message": f"Fish Audio did not return audio bytes: {error_json}",
                                },
                            }
                    else:
                        err_text = res.text[:200]
                        logger.warning(f"Fish Audio TTS returned HTTP {res.status_code}: {err_text}")
                        return {
                            "success": False,
                            "provider": "fish_audio",
                            "audio_base64": None,
                            "audio_format": "mp3",
                            "language": norm_lang,
                            "voice_id": effective_voice,
                            "error": {
                                "code": f"HTTP_{res.status_code}",
                                "message": f"Fish Audio TTS error: {err_text}",
                            },
                        }
            except Exception as exc:
                logger.error(f"Fish Audio TTS request failed: {exc}")
                return {
                    "success": False,
                    "provider": "fish_audio",
                    "audio_base64": None,
                    "audio_format": "mp3",
                    "language": norm_lang,
                    "voice_id": voice_id,
                    "error": {
                        "code": "TTS_NETWORK_ERROR",
                        "message": str(exc),
                    },
                }

        return {
            "success": False,
            "provider": provider,
            "audio_base64": None,
            "audio_format": "mp3",
            "language": norm_lang,
            "voice_id": voice_id,
            "error": {
                "code": "TTS_NOT_CONFIGURED",
                "message": "Fish Audio API key is not configured.",
            },
        }

    async def health_check_stt(self) -> Dict[str, Any]:
        """Check Groq STT reachability."""
        if not settings.STT_API_KEY:
            return {
                "provider": "groq",
                "configured": False,
                "reachable": False,
                "model": settings.STT_MODEL,
                "error": "STT_KEY_MISSING",
                "latency_ms": 0,
            }

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {settings.STT_API_KEY}"},
                )
                latency_ms = int((time.time() - start) * 1000)
                if res.status_code == 200:
                    return {
                        "provider": "groq",
                        "configured": True,
                        "reachable": True,
                        "model": settings.STT_MODEL,
                        "latency_ms": latency_ms,
                        "error": None,
                    }
                else:
                    return {
                        "provider": "groq",
                        "configured": True,
                        "reachable": False,
                        "model": settings.STT_MODEL,
                        "latency_ms": latency_ms,
                        "error": f"HTTP {res.status_code}",
                    }
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "provider": "groq",
                "configured": True,
                "reachable": False,
                "model": settings.STT_MODEL,
                "latency_ms": latency_ms,
                "error": str(e)[:150],
            }

    async def health_check_tts(self) -> Dict[str, Any]:
        """Check Fish Audio TTS reachability."""
        api_key = settings.get_effective_tts_key()
        model = settings.get_effective_tts_model()
        if not api_key:
            return {
                "provider": "fish_audio",
                "configured": False,
                "reachable": False,
                "model": model,
                "voice_configured": bool(settings.FISH_AUDIO_VOICE_ID),
                "error": "TTS_KEY_MISSING",
                "latency_ms": 0,
            }

        start = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    "https://api.fish.audio/wallet/self/api-credit",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                latency_ms = int((time.time() - start) * 1000)
                if res.status_code in (200, 402):
                    return {
                        "provider": "fish_audio",
                        "configured": True,
                        "reachable": True,
                        "model": model,
                        "voice_configured": bool(settings.FISH_AUDIO_VOICE_ID),
                        "latency_ms": latency_ms,
                        "error": None,
                    }
                else:
                    return {
                        "provider": "fish_audio",
                        "configured": True,
                        "reachable": False,
                        "model": model,
                        "voice_configured": bool(settings.FISH_AUDIO_VOICE_ID),
                        "latency_ms": latency_ms,
                        "error": f"HTTP {res.status_code}",
                    }
        except Exception as e:
            latency_ms = int((time.time() - start) * 1000)
            return {
                "provider": "fish_audio",
                "configured": True,
                "reachable": False,
                "model": model,
                "voice_configured": bool(settings.FISH_AUDIO_VOICE_ID),
                "latency_ms": latency_ms,
                "error": str(e)[:150],
            }


voice_service = VoiceService()
