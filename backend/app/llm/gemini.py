import google.generativeai as genai
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model
        self._model = genai.GenerativeModel(self._model_name)

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._model.generate_content_async(
            [system_prompt, user_prompt]
        )
        usage = response.usage_metadata
        return LLMResponse(
            text=response.text,
            tokens_in=usage.prompt_token_count if usage else 0,
            tokens_out=usage.candidates_token_count if usage else 0,
            model=self._model_name,
        )
