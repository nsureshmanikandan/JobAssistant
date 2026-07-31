from functools import lru_cache
from app.config import settings
from app.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "azure_openai":
        from app.llm.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    if provider == "claude":
        from app.llm.claude import ClaudeProvider
        return ClaudeProvider()
    if provider == "gemini":
        from app.llm.gemini import GeminiProvider
        return GeminiProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
