from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel


class LLMProvider(ABC):
    """
    Abstract LLM Provider interface.
    Allows switching model providers (Gemini, local, mock) without altering business logic.
    """

    @abstractmethod
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        schema: Type[BaseModel],
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> BaseModel:
        pass

    @abstractmethod
    async def translate(self, text: str, target_lang: str) -> str:
        pass
