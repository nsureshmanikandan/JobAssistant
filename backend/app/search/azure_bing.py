import httpx
from app.config import settings
from app.search.base import SearchProvider, SearchResult


class AzureBingSearchProvider(SearchProvider):
    name = "azure_bing"

    def __init__(self, api_key: str | None = None, endpoint: str | None = None) -> None:
        self._api_key = api_key or settings.azure_bing_search_key
        self._endpoint = (endpoint or settings.azure_bing_search_endpoint).rstrip("/")

    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        if not self._api_key or not self._endpoint:
            raise ValueError(
                "Azure Bing Search is not configured — set AZURE_BING_SEARCH_KEY and "
                "AZURE_BING_SEARCH_ENDPOINT in .env, or switch SEARCH_PROVIDER to google_custom."
            )
        freshness = "Day" if freshness_hours <= 24 else "Week" if freshness_hours <= 168 else "Month"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self._endpoint}/v7.0/search",
                params={"q": query, "freshness": freshness, "count": 20},
                headers={"Ocp-Apim-Subscription-Key": self._api_key},
            )
            response.raise_for_status()
            data = response.json()
        pages = data.get("webPages", {}).get("value", [])
        return [
            SearchResult(title=p["name"], url=p["url"], snippet=p.get("snippet", ""))
            for p in pages
        ]
