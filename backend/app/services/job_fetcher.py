from dataclasses import dataclass
import httpx
from readability import Document
from bs4 import BeautifulSoup


@dataclass
class FetchResult:
    description: str | None
    needs_manual_paste: bool


async def fetch_job_page(url: str) -> FetchResult:
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; JobAssistant/1.0)"},
            )
        if response.status_code != 200:
            return FetchResult(description=None, needs_manual_paste=True)
        doc = Document(response.text)
        soup = BeautifulSoup(doc.summary(), "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if not text:
            return FetchResult(description=None, needs_manual_paste=True)
        return FetchResult(description=text, needs_manual_paste=False)
    except httpx.HTTPError:
        return FetchResult(description=None, needs_manual_paste=True)
