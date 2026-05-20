from backend.app.ai.providers.base import AIProvider
from backend.app.ai.providers.local import LocalProvider
from backend.app.ai.providers.openai_provider import OpenAIProvider
from backend.app.core.config import get_settings


def get_provider() -> AIProvider:
    settings = get_settings()
    if settings.llm_enabled and settings.openai_api_key and settings.ai_provider.lower() == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, model_name=settings.ai_model_name)
    provider = LocalProvider()
    provider.model_name = settings.ai_model_name or provider.model_name
    return provider
