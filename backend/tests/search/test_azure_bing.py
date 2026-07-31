import pytest
import respx
from httpx import Response
from app.search.azure_bing import AzureBingSearchProvider


@pytest.mark.asyncio
@respx.mock
async def test_azure_bing_parses_results():
    provider = AzureBingSearchProvider(api_key="fake-key", endpoint="https://fake.bing.example")
    respx.get("https://fake.bing.example/v7.0/search").mock(
        return_value=Response(
            200,
            json={
                "webPages": {
                    "value": [
                        {
                            "name": "GenAI Architect at Acme",
                            "url": "https://linkedin.com/jobs/view/123",
                            "snippet": "Acme is hiring a GenAI Architect in Chennai",
                        }
                    ]
                }
            },
        )
    )
    results = await provider.search("site:linkedin.com/jobs GenAI Architect Chennai")
    assert len(results) == 1
    assert results[0].url == "https://linkedin.com/jobs/view/123"


@pytest.mark.asyncio
async def test_azure_bing_raises_clear_error_when_unconfigured():
    provider = AzureBingSearchProvider(api_key="", endpoint="")
    with pytest.raises(ValueError, match="Azure Bing Search is not configured"):
        await provider.search("some query")
