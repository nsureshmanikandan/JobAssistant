from openai import AsyncAzureOpenAI
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse


class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = response.choices[0].message.content or ""
        return LLMResponse(
            text=choice,
            tokens_in=response.usage.prompt_tokens if response.usage else 0,
            tokens_out=response.usage.completion_tokens if response.usage else 0,
            model=self._deployment,
        )
