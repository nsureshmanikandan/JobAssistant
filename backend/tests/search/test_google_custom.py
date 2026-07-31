import pytest
import respx
from httpx import Response
from app.search.google_custom import GoogleCustomSearchProvider


@pytest.mark.asyncio
@respx.mock
async def test_google_custom_parses_results():
    provider = GoogleCustomSearchProvider(api_key="fake-key", cx="fake-cx")
    respx.get("https://www.googleapis.com/customsearch/v1").mock(
        return_value=Response(
            200,
            json={"items": [{"title": "GenAI Architect at Acme", "link": "https://naukri.com/job/1", "snippet": "..."}]},
        )
    )
    results = await provider.search("GenAI Architect Chennai")
    assert len(results) == 1
    assert results[0].url == "https://naukri.com/job/1"


@pytest.mark.asyncio
async def test_google_custom_raises_clear_error_when_unconfigured():
    provider = GoogleCustomSearchProvider(api_key="", cx="")
    with pytest.raises(ValueError, match="Google Custom Search is not configured"):
        await provider.search("some query")
