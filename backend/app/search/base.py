from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        raise NotImplementedError
