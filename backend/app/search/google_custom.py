import httpx
from app.config import settings
from app.search.base import SearchProvider, SearchResult

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleCustomSearchProvider(SearchProvider):
    name = "google_custom"

    def __init__(self, api_key: str | None = None, cx: str | None = None) -> None:
        # `is not None` (not `or`) so tests can pass "" to force the unconfigured
        # path even when real .env settings are non-empty.
        self._api_key = api_key if api_key is not None else settings.google_custom_search_api_key
        self._cx = cx if cx is not None else settings.google_custom_search_cx

    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        if not self._api_key or not self._cx:
            raise ValueError(
                "Google Custom Search is not configured — set GOOGLE_CUSTOM_SEARCH_API_KEY and "
                "GOOGLE_CUSTOM_SEARCH_CX in .env, or switch SEARCH_PROVIDER to azure_bing."
            )
        days = max(1, -(-freshness_hours // 24))  # ceil division: 48h -> 2, 72h -> 3, 168h -> 7
        date_restrict = f"d{days}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                _ENDPOINT,
                params={
                    "key": self._api_key,
                    "cx": self._cx,
                    "q": query,
                    "dateRestrict": date_restrict,
                    "num": 10,
                },
            )
            response.raise_for_status()
            data = response.json()
        items = data.get("items", [])
        return [
            SearchResult(title=i["title"], url=i["link"], snippet=i.get("snippet", ""))
            for i in items
        ]
