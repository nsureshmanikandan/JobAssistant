import httpx
from app.config import settings
from app.search.base import SearchProvider, SearchResult

_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


class GoogleCustomSearchProvider(SearchProvider):
    name = "google_custom"

    def __init__(self, api_key: str | None = None, cx: str | None = None) -> None:
        self._api_key = api_key or settings.google_custom_search_api_key
        self._cx = cx or settings.google_custom_search_cx

    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        date_restrict = "d1" if freshness_hours <= 24 else "w1"
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
