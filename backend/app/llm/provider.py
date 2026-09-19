from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class GeminiErrorCode:
    GEMINI_AUTH_ERROR = "GEMINI_AUTH_ERROR"
    GEMINI_QUOTA_ERROR = "GEMINI_QUOTA_ERROR"
    GEMINI_MODEL_ERROR = "GEMINI_MODEL_ERROR"
    GEMINI_TIMEOUT = "GEMINI_TIMEOUT"
    GEMINI_NETWORK_ERROR = "GEMINI_NETWORK_ERROR"
    GEMINI_INVALID_REQUEST = "GEMINI_INVALID_REQUEST"
    GEMINI_UNKNOWN_ERROR = "GEMINI_UNKNOWN_ERROR"


class LLMError(Exception):
    def __init__(self, code: str, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.original_error = original_error


class LLMProvider(ABC):
    """
    Abstract LLM Provider interface.
    Allows switching model providers (Gemini, local, mock) without altering business logic.
    """

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        language: Optional[str] = None,
    ) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        schema: Type[BaseModel],
        prompt: str,
        system_prompt: Optional[str] = None,
        language: Optional[str] = None,
    ) -> BaseModel:
        pass

    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health and reachability of the provider.
        Returns:
            {"provider": "gemini", "configured": bool, "reachable": bool, "model": str, "latency_ms": int, "error": Optional[str]}
        """
        pass
