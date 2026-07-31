import pytest
import respx
from httpx import Response
from app.search.apify import ApifyJobsProvider, _parse_query, _published_at_code


def test_parse_query_extracts_site_title_location():
    site, title, location = _parse_query('site:linkedin.com/jobs "GenAI Architect" Chennai')
    assert site == "linkedin.com/jobs"
    assert title == "GenAI Architect"
    assert location == "Chennai"


def test_parse_query_raises_on_unexpected_format():
    with pytest.raises(ValueError, match="Could not parse query"):
        _parse_query("not a real query")


@pytest.mark.parametrize(
    "hours,expected",
    [(24, "r86400"), (48, "r604800"), (168, "r604800"), (720, "r2592000")],
)
def test_published_at_code_maps_freshness_hours(hours, expected):
    assert _published_at_code(hours) == expected


@pytest.mark.asyncio
async def test_apify_raises_clear_error_when_unconfigured():
    provider = ApifyJobsProvider(api_token="", actor_id="")
    with pytest.raises(ValueError, match="Apify is not configured"):
        await provider.search('site:linkedin.com/jobs "GenAI Architect" Chennai')


@pytest.mark.asyncio
async def test_apify_skips_non_linkedin_queries_without_calling_api():
    provider = ApifyJobsProvider(api_token="fake-token", actor_id="cheap_scraper/linkedin-job-scraper")
    # No respx mock registered — if the provider tried to call the API this would raise.
    results = await provider.search('site:naukri.com "GenAI Architect" Chennai')
    assert results == []


@pytest.mark.asyncio
@respx.mock
async def test_apify_parses_linkedin_results():
    provider = ApifyJobsProvider(api_token="fake-token", actor_id="cheap_scraper/linkedin-job-scraper")
    respx.post("https://api.apify.com/v2/acts/cheap_scraper~linkedin-job-scraper/run-sync-get-dataset-items").mock(
        return_value=Response(
            200,
            json=[
                {
                    "jobTitle": "GenAI Architect",
                    "companyName": "Acme Corp",
                    "location": "Chennai",
                    "jobUrl": "https://linkedin.com/jobs/view/123",
                    "jobDescription": "We are hiring a GenAI Architect...",
                }
            ],
        )
    )
    results = await provider.search('site:linkedin.com/jobs "GenAI Architect" Chennai')
    assert len(results) == 1
    assert results[0].url == "https://linkedin.com/jobs/view/123"
    assert "Acme Corp" in results[0].title


@pytest.mark.asyncio
@respx.mock
async def test_apify_skips_items_with_no_url():
    provider = ApifyJobsProvider(api_token="fake-token", actor_id="cheap_scraper/linkedin-job-scraper")
    respx.post("https://api.apify.com/v2/acts/cheap_scraper~linkedin-job-scraper/run-sync-get-dataset-items").mock(
        return_value=Response(200, json=[{"jobTitle": "GenAI Architect", "companyName": "Acme"}])
    )
    results = await provider.search('site:linkedin.com/jobs "GenAI Architect" Chennai')
    assert results == []
