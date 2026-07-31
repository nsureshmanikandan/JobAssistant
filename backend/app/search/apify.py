import re
import httpx
from app.config import settings
from app.search.base import SearchProvider, SearchResult

_BASE_URL = "https://api.apify.com/v2"

# build_queries() (app/criteria.py) produces engine-agnostic queries shaped
# for a generic web search API: 'site:{site} "{title}" {location}'. This
# provider instead calls a LinkedIn-specific Apify actor (cheap_scraper/
# linkedin-job-scraper — pay-per-result, ~$0.35-0.70/1000 results, no monthly
# rental) whose input is {keyword, locations} — no "site:" concept. We parse
# the query back apart and only act on the linkedin.com/jobs variant; the
# naukri.com/indeed.com variants of the same title+location are skipped here
# (return no results) rather than paying for three duplicate actor runs.
_QUERY_PATTERN = re.compile(r'site:(\S+)\s+"([^"]+)"\s+(.+)')

# The actor enforces maxItems >= 150 (confirmed via a live 400 response: "Field
# input.maxItems must be >= 150"). This is a ceiling, not a target — pricing is
# per result actually returned, not per maxItems requested, so a query with 5
# real matches is only billed for 5.
_MIN_MAX_ITEMS = 150


def _parse_query(query: str) -> tuple[str, str, str]:
    match = _QUERY_PATTERN.match(query)
    if not match:
        raise ValueError(f"Could not parse query for Apify provider: {query!r}")
    site, title, location = match.groups()
    return site, title.strip(), location.strip()


def _published_at_code(freshness_hours: int) -> str:
    if freshness_hours <= 24:
        return "r86400"
    if freshness_hours <= 168:
        return "r604800"
    return "r2592000"


class ApifyJobsProvider(SearchProvider):
    name = "apify"

    def __init__(self, api_token: str | None = None, actor_id: str | None = None) -> None:
        # `is not None` (not `or`) so tests can explicitly pass "" to simulate an
        # unconfigured provider even when the real .env has a non-empty value —
        # `"" or settings.x` would silently fall back to the real setting instead.
        self._api_token = api_token if api_token is not None else settings.apify_api_token
        raw_actor_id = actor_id if actor_id is not None else settings.apify_actor_id
        self._actor_id = raw_actor_id.replace("/", "~") if raw_actor_id else raw_actor_id

    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        if not self._api_token or not self._actor_id:
            raise ValueError(
                "Apify is not configured — set APIFY_API_TOKEN and APIFY_ACTOR_ID in .env "
                "(e.g. APIFY_ACTOR_ID=cheap_scraper/linkedin-job-scraper)."
            )
        site, title, location = _parse_query(query)
        if site != "linkedin.com/jobs":
            return []

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{_BASE_URL}/acts/{self._actor_id}/run-sync-get-dataset-items",
                params={"token": self._api_token},
                json={
                    "keyword": [title],
                    "locations": [location],
                    "maxItems": _MIN_MAX_ITEMS,
                    "publishedAt": _published_at_code(freshness_hours),
                },
            )
            response.raise_for_status()
            items = response.json()

        results = []
        for item in items:
            url = item.get("jobUrl") or item.get("applyUrl")
            if not url:
                continue
            job_title = item.get("jobTitle", title)
            company = item.get("companyName", "Unknown")
            results.append(
                SearchResult(
                    title=f"{job_title} at {company}",
                    url=url,
                    snippet=(item.get("jobDescription") or "")[:300],
                )
            )
        return results
