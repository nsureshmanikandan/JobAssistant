from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return the raw text completion plus token usage."""
        raise NotImplementedError
