from backend.app.config import settings
from backend.app.llm.provider import LLMProvider
from backend.app.llm.gemini_provider import GeminiProvider, llm_provider


def get_llm_provider() -> LLMProvider:
    """
    Returns the configured LLM provider instance.
    """
    provider_name = (settings.LLM_PROVIDER or "gemini").lower()
    if provider_name == "gemini":
        return llm_provider
    # Fallback to default Gemini provider
    return llm_provider
