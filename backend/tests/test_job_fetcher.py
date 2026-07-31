import pytest
import respx
from httpx import Response
from app.services.job_fetcher import fetch_job_page


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_extracts_description():
    respx.get("https://example.com/job/1").mock(
        return_value=Response(
            200,
            html="<html><body><main><p>We need a GenAI Architect.</p></main></body></html>",
        )
    )
    result = await fetch_job_page("https://example.com/job/1")
    assert result.needs_manual_paste is False
    assert "GenAI Architect" in result.description


@pytest.mark.asyncio
@respx.mock
async def test_fetch_job_page_flags_manual_paste_on_block():
    respx.get("https://example.com/job/2").mock(return_value=Response(403))
    result = await fetch_job_page("https://example.com/job/2")
    assert result.needs_manual_paste is True
    assert result.description is None
