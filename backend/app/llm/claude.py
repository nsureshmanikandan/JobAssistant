from anthropic import AsyncAnthropic
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse

_MODEL = "claude-sonnet-5"


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=_MODEL,
        )
