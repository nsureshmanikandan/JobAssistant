from functools import lru_cache
from app.config import settings
from app.search.base import SearchProvider


@lru_cache
def get_search_provider() -> SearchProvider:
    provider = settings.search_provider
    if provider == "azure_bing":
        from app.search.azure_bing import AzureBingSearchProvider
        return AzureBingSearchProvider()
    if provider == "google_custom":
        from app.search.google_custom import GoogleCustomSearchProvider
        return GoogleCustomSearchProvider()
    if provider == "apify":
        from app.search.apify import ApifyJobsProvider
        return ApifyJobsProvider()
    raise ValueError(f"Unknown SEARCH_PROVIDER: {provider}")
