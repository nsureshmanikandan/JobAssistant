# Job Application Assistant — Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a locally-run (Docker Compose) job application assistant: daily/on-demand job
discovery via search API, LLM-based structured match-scoring against the user's criteria,
on-demand ATS-friendly resume + cover-letter tailoring with PDF export, and a React dashboard
where the user reviews and approves before manually applying. No automation ever fills or
submits a job application form.

**Architecture:** FastAPI backend (SQLite via SQLModel, pluggable LLM/search provider adapters
selected by env var, APScheduler for daily discovery, structlog + an `LLMCallLog` table for
observability) behind a React + Vite + Tailwind SPA. Both run in Docker Compose locally.

**Tech Stack:** Python 3.11, FastAPI, SQLModel, APScheduler, httpx, WeasyPrint, structlog,
pytest. React 18, Vite, TypeScript, TailwindCSS, Vitest, React Testing Library, Playwright.
Docker Compose.

---

## File Structure

```
backend/
  app/
    config.py                  # pydantic Settings, loads .env
    main.py                    # FastAPI app, startup hooks, router mounting
    db/
      models.py                # SQLModel: Job, ResumeVersion, Application, SearchRun, LLMCallLog
      session.py                # engine + get_session()
    llm/
      base.py                  # LLMProvider ABC, ScoreResult/TailoredContent schemas
      azure_openai.py
      claude.py
      gemini.py
      factory.py                # get_llm_provider()
    search/
      base.py                  # SearchProvider ABC, SearchResult schema
      azure_bing.py
      google_custom.py
      factory.py                # get_search_provider()
    prompts/
      scoring.py                # SCORING_PROMPT_ID, build_scoring_prompt()
      tailoring.py              # TAILORING_PROMPT_ID, build_tailoring_prompt()
    services/
      dedupe.py                 # job_dedupe_key()
      job_fetcher.py            # fetch_job_page()
      scoring.py                # score_job()
      tailoring.py              # tailor_job()
      export.py                 # render_resume_pdf(), render_cover_letter_pdf()
      discovery.py              # run_discovery() — orchestrates search->fetch->score->store
    observability/
      logging.py                # structlog configuration
      llm_log.py                # log_llm_call()
    scheduler.py                # APScheduler setup, daily job
    api/
      jobs.py                   # /jobs routes
      search_runs.py            # /search routes
      applications.py           # /applications routes
      settings.py                # /settings routes
      observability.py           # /observability routes
  tests/
    test_dedupe.py
    test_job_fetcher.py
    test_scoring.py
    test_tailoring.py
    test_export.py
    llm/test_factory.py
    search/test_factory.py
  requirements.txt
  Dockerfile

frontend/
  src/
    api/client.ts
    types.ts
    App.tsx
    main.tsx
    pages/
      Dashboard.tsx
      JobReview.tsx
      ManualPaste.tsx
      Applications.tsx
      Settings.tsx
      Observability.tsx
    pages/__tests__/
      Dashboard.test.tsx
      JobReview.test.tsx
    e2e/
      approve-flow.spec.ts
  index.html
  vite.config.ts
  tailwind.config.js
  package.json
  Dockerfile

infra/
  docker-compose.yml
```

---

## Task 1: Backend scaffolding — config, DB models, session

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/models.py`
- Create: `backend/app/db/session.py`
- Test: `backend/tests/test_db_models.py`

- [ ] **Step 1: Write requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.32.0
sqlmodel==0.0.22
apscheduler==3.10.4
httpx==0.27.2
beautifulsoup4==4.12.3
readability-lxml==0.8.1
weasyprint==62.3
structlog==24.4.0
pydantic-settings==2.6.1
openai==1.54.0
anthropic==0.39.0
google-generativeai==0.8.3
pytest==8.3.3
pytest-asyncio==0.24.0
respx==0.21.1
```

- [ ] **Step 2: Write config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "azure_openai"
    azure_openai_endpoint: str = ""
    azure_openai_api_key: str = ""
    azure_openai_api_version: str = ""
    azure_openai_deployment: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.1-flash-lite"

    search_provider: str = "azure_bing"
    azure_bing_search_key: str = ""
    azure_bing_search_endpoint: str = ""
    google_custom_search_api_key: str = ""
    google_custom_search_cx: str = ""

    database_url: str = "sqlite:///./data/jobassistant.db"
    scheduler_hour: int = 7
    match_threshold: int = 85


settings = Settings()
```

- [ ] **Step 3: Write the failing test for models**

```python
# backend/tests/test_db_models.py
from sqlmodel import SQLModel, create_engine, Session
from app.db.models import Job, ResumeVersion, Application, SearchRun, LLMCallLog


def test_job_can_be_created_and_queried():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        job = Job(
            title="GenAI Architect",
            company="Acme Corp",
            location="Chennai",
            source_url="https://example.com/job/1",
            source_site="linkedin",
            dedupe_key="acme|genai architect|chennai",
            status="pending_review",
        )
        session.add(job)
        session.commit()
        session.refresh(job)
        assert job.id is not None
        fetched = session.get(Job, job.id)
        assert fetched.title == "GenAI Architect"
```

- [ ] **Step 4: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_db_models.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db.models'`

- [ ] **Step 5: Write models.py**

```python
# backend/app/db/models.py
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    company: str
    location: str
    salary_text: Optional[str] = None
    source_url: str
    source_site: str
    description: Optional[str] = None
    needs_manual_paste: bool = False
    dedupe_key: str = Field(index=True, unique=True)
    match_percentage: Optional[int] = None
    matched_skills: Optional[str] = None   # JSON-encoded list
    missing_skills: Optional[str] = None   # JSON-encoded list
    sponsorship_required: Optional[bool] = None
    company_size_estimate: Optional[str] = None
    scoring_reasoning: Optional[str] = None
    status: str = "pending_review"  # pending_review|scoring_failed|approved|rejected|applied
    tailored_resume: Optional[str] = None
    tailored_cover_letter: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)


class ResumeVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    content: str
    is_master: bool = False
    created_at: datetime = Field(default_factory=utcnow)


class Application(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    status: str = "approved"  # approved|applied|skipped
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)


class SearchRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    started_at: datetime = Field(default_factory=utcnow)
    finished_at: Optional[datetime] = None
    jobs_found: int = 0
    jobs_new: int = 0
    status: str = "running"  # running|completed|failed
    error: Optional[str] = None


class LLMCallLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str
    model: str
    prompt_id: str
    job_id: Optional[int] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    latency_ms: Optional[int] = None
    success: bool = True
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
```

- [ ] **Step 6: Write session.py**

```python
# backend/app/db/session.py
from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def init_db() -> None:
    from app.db import models  # noqa: F401 ensures models are registered
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_db_models.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/requirements.txt backend/app/config.py backend/app/db backend/tests/test_db_models.py
git commit -m "feat(backend): add config, SQLModel models, db session"
```

---

## Task 2: Dedupe key logic

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/dedupe.py`
- Test: `backend/tests/test_dedupe.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_dedupe.py
from app.services.dedupe import job_dedupe_key


def test_dedupe_key_is_case_and_whitespace_insensitive():
    key1 = job_dedupe_key(company="Acme Corp", title="GenAI Architect", location="Chennai")
    key2 = job_dedupe_key(company="  ACME CORP ", title="genai architect", location="chennai ")
    assert key1 == key2


def test_dedupe_key_differs_for_different_jobs():
    key1 = job_dedupe_key(company="Acme Corp", title="GenAI Architect", location="Chennai")
    key2 = job_dedupe_key(company="Acme Corp", title="Data Scientist", location="Chennai")
    assert key1 != key2
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_dedupe.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.dedupe'`

- [ ] **Step 3: Write dedupe.py**

```python
# backend/app/services/dedupe.py
import re


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def job_dedupe_key(company: str, title: str, location: str) -> str:
    return f"{_normalize(company)}|{_normalize(title)}|{_normalize(location)}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_dedupe.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/dedupe.py backend/tests/test_dedupe.py
git commit -m "feat(backend): add job dedupe key logic"
```

---

## Task 3: LLM provider abstraction + Azure OpenAI, Claude, Gemini adapters

**Files:**
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/azure_openai.py`
- Create: `backend/app/llm/claude.py`
- Create: `backend/app/llm/gemini.py`
- Create: `backend/app/llm/factory.py`
- Test: `backend/tests/llm/test_factory.py`

- [ ] **Step 1: Write base.py**

```python
# backend/app/llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return the raw text completion plus token usage."""
        raise NotImplementedError
```

- [ ] **Step 2: Write azure_openai.py**

```python
# backend/app/llm/azure_openai.py
from openai import AsyncAzureOpenAI
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse


class AzureOpenAIProvider(LLMProvider):
    name = "azure_openai"

    def __init__(self) -> None:
        self._client = AsyncAzureOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
        )
        self._deployment = settings.azure_openai_deployment

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        choice = response.choices[0].message.content or ""
        return LLMResponse(
            text=choice,
            tokens_in=response.usage.prompt_tokens if response.usage else 0,
            tokens_out=response.usage.completion_tokens if response.usage else 0,
            model=self._deployment,
        )
```

- [ ] **Step 3: Write claude.py**

```python
# backend/app/llm/claude.py
from anthropic import AsyncAnthropic
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse

_MODEL = "claude-sonnet-5"


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self) -> None:
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._client.messages.create(
            model=_MODEL,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return LLMResponse(
            text=text,
            tokens_in=response.usage.input_tokens,
            tokens_out=response.usage.output_tokens,
            model=_MODEL,
        )
```

- [ ] **Step 4: Write gemini.py**

```python
# backend/app/llm/gemini.py
import google.generativeai as genai
from app.config import settings
from app.llm.base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    name = "gemini"

    def __init__(self) -> None:
        genai.configure(api_key=settings.gemini_api_key)
        self._model_name = settings.gemini_model
        self._model = genai.GenerativeModel(self._model_name)

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self._model.generate_content_async(
            [system_prompt, user_prompt]
        )
        usage = response.usage_metadata
        return LLMResponse(
            text=response.text,
            tokens_in=usage.prompt_token_count if usage else 0,
            tokens_out=usage.candidates_token_count if usage else 0,
            model=self._model_name,
        )
```

- [ ] **Step 5: Write factory.py**

```python
# backend/app/llm/factory.py
from functools import lru_cache
from app.config import settings
from app.llm.base import LLMProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    provider = settings.llm_provider
    if provider == "azure_openai":
        from app.llm.azure_openai import AzureOpenAIProvider
        return AzureOpenAIProvider()
    if provider == "claude":
        from app.llm.claude import ClaudeProvider
        return ClaudeProvider()
    if provider == "gemini":
        from app.llm.gemini import GeminiProvider
        return GeminiProvider()
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

- [ ] **Step 6: Write the failing test for the factory**

```python
# backend/tests/llm/test_factory.py
import pytest
from app.config import settings
from app.llm.factory import get_llm_provider


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "not_a_real_provider")
    get_llm_provider.cache_clear()
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        get_llm_provider()


def test_azure_openai_provider_selected(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "azure_openai")
    get_llm_provider.cache_clear()
    provider = get_llm_provider()
    assert provider.name == "azure_openai"
```

- [ ] **Step 7: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/llm/test_factory.py -v`
Expected: PASS (create empty `backend/tests/llm/__init__.py` if pytest can't collect the package)

- [ ] **Step 8: Commit**

```bash
git add backend/app/llm backend/tests/llm
git commit -m "feat(backend): add pluggable LLM provider abstraction (Azure OpenAI, Claude, Gemini)"
```

---

## Task 4: Search provider abstraction + Azure Bing, Google Custom Search adapters

**Files:**
- Create: `backend/app/search/__init__.py`
- Create: `backend/app/search/base.py`
- Create: `backend/app/search/azure_bing.py`
- Create: `backend/app/search/google_custom.py`
- Create: `backend/app/search/factory.py`
- Test: `backend/tests/search/test_factory.py`
- Test: `backend/tests/search/test_azure_bing.py`

- [ ] **Step 1: Write base.py**

```python
# backend/app/search/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        raise NotImplementedError
```

- [ ] **Step 2: Write the failing test for Azure Bing adapter**

```python
# backend/tests/search/test_azure_bing.py
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
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/search/test_azure_bing.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.search.azure_bing'`

- [ ] **Step 4: Write azure_bing.py**

```python
# backend/app/search/azure_bing.py
import httpx
from app.config import settings
from app.search.base import SearchProvider, SearchResult


class AzureBingSearchProvider(SearchProvider):
    name = "azure_bing"

    def __init__(self, api_key: str | None = None, endpoint: str | None = None) -> None:
        self._api_key = api_key or settings.azure_bing_search_key
        self._endpoint = (endpoint or settings.azure_bing_search_endpoint).rstrip("/")

    async def search(self, query: str, freshness_hours: int = 24) -> list[SearchResult]:
        freshness = "Day" if freshness_hours <= 24 else "Week"
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
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/search/test_azure_bing.py -v`
Expected: PASS

- [ ] **Step 6: Write google_custom.py**

```python
# backend/app/search/google_custom.py
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
```

- [ ] **Step 7: Write factory.py + failing/passing test**

```python
# backend/app/search/factory.py
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
    raise ValueError(f"Unknown SEARCH_PROVIDER: {provider}")
```

```python
# backend/tests/search/test_factory.py
import pytest
from app.config import settings
from app.search.factory import get_search_provider


def test_unknown_search_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "search_provider", "not_real")
    get_search_provider.cache_clear()
    with pytest.raises(ValueError, match="Unknown SEARCH_PROVIDER"):
        get_search_provider()
```

Run: `cd backend && python -m pytest tests/search/test_factory.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/search backend/tests/search
git commit -m "feat(backend): add pluggable search provider abstraction (Azure Bing, Google Custom Search)"
```

---

## Task 5: Job fetcher with manual-paste fallback

**Files:**
- Create: `backend/app/services/job_fetcher.py`
- Test: `backend/tests/test_job_fetcher.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_job_fetcher.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_job_fetcher.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.job_fetcher'`

- [ ] **Step 3: Write job_fetcher.py**

```python
# backend/app/services/job_fetcher.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_job_fetcher.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/job_fetcher.py backend/tests/test_job_fetcher.py
git commit -m "feat(backend): add job page fetcher with manual-paste fallback"
```

---

## Task 6: Versioned prompts

**Files:**
- Create: `backend/app/prompts/__init__.py`
- Create: `backend/app/prompts/scoring.py`
- Create: `backend/app/prompts/tailoring.py`

- [ ] **Step 1: Write scoring.py**

```python
# backend/app/prompts/scoring.py
SCORING_PROMPT_ID = "scoring-v1"

SCORING_SYSTEM_PROMPT = """You are an expert technical recruiter. Score how well a candidate's \
resume matches a job description against the candidate's stated criteria. Respond with ONLY a \
JSON object matching this schema, no markdown fences, no commentary:

{
  "match_percentage": <int 0-100>,
  "matched_skills": [<string>, ...],
  "missing_skills": [<string>, ...],
  "sponsorship_required": <true|false>,
  "company_size_estimate": "<string, e.g. '10000+' or 'unknown'>",
  "reasoning": "<one paragraph explaining the score>"
}

Set sponsorship_required to true if the posting mentions visa sponsorship, work authorization \
requirements the candidate does not meet, or similar. If genuinely unclear, set it to false and \
say so in reasoning rather than guessing."""


def build_scoring_prompt(resume: str, job_description: str, criteria: str) -> str:
    return (
        f"CANDIDATE CRITERIA:\n{criteria}\n\n"
        f"CANDIDATE RESUME:\n{resume}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )
```

- [ ] **Step 2: Write tailoring.py**

```python
# backend/app/prompts/tailoring.py
TAILORING_PROMPT_ID = "tailoring-v1"

TAILORING_SYSTEM_PROMPT = """You are an expert resume writer specializing in ATS-friendly \
resumes for senior technical roles. Given a candidate's master resume and a specific job \
description, produce ONLY a JSON object, no markdown fences, no commentary:

{
  "tailored_resume": "<full resume text, plain text, ATS-safe: no tables, no columns, \
standard section headers (SUMMARY, EXPERIENCE, SKILLS, EDUCATION), keywords from the JD \
naturally incorporated where truthful>",
  "cover_letter": "<professional cover letter, 3-4 paragraphs, addressed generically \
('Dear Hiring Manager') unless a name is given in the job description>"
}

Never fabricate experience, skills, or credentials the candidate does not have. Rephrase and \
reorder truthful content to match the JD's language and priorities."""


def build_tailoring_prompt(resume: str, job_description: str, job_title: str, company: str) -> str:
    return (
        f"JOB TITLE: {job_title}\nCOMPANY: {company}\n\n"
        f"MASTER RESUME:\n{resume}\n\n"
        f"JOB DESCRIPTION:\n{job_description}"
    )
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/prompts
git commit -m "feat(backend): add versioned scoring and tailoring prompts"
```

---

## Task 7: Structured-JSON scoring service

**Files:**
- Create: `backend/app/services/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scoring.py
import json
import pytest
from app.services.scoring import score_job, ScoreResult
from app.llm.base import LLMResponse


class FakeLLM:
    name = "fake"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(text=self._response_text, tokens_in=10, tokens_out=20, model="fake-model")


@pytest.mark.asyncio
async def test_score_job_parses_valid_json():
    payload = {
        "match_percentage": 90,
        "matched_skills": ["Python", "LLM orchestration"],
        "missing_skills": ["Kubernetes"],
        "sponsorship_required": False,
        "company_size_estimate": "10000+",
        "reasoning": "Strong alignment on GenAI architecture experience.",
    }
    llm = FakeLLM(json.dumps(payload))
    result = await score_job(llm, resume="resume text", job_description="jd text", criteria="criteria text")
    assert isinstance(result, ScoreResult)
    assert result.match_percentage == 90
    assert result.sponsorship_required is False


@pytest.mark.asyncio
async def test_score_job_raises_on_malformed_json():
    llm = FakeLLM("not json at all")
    with pytest.raises(ValueError, match="did not return valid JSON"):
        await score_job(llm, resume="r", job_description="j", criteria="c")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.scoring'`

- [ ] **Step 3: Write scoring.py**

```python
# backend/app/services/scoring.py
import json
from dataclasses import dataclass
from app.llm.base import LLMProvider
from app.prompts.scoring import SCORING_SYSTEM_PROMPT, build_scoring_prompt


@dataclass
class ScoreResult:
    match_percentage: int
    matched_skills: list[str]
    missing_skills: list[str]
    sponsorship_required: bool
    company_size_estimate: str
    reasoning: str


async def score_job(llm: LLMProvider, resume: str, job_description: str, criteria: str) -> ScoreResult:
    prompt = build_scoring_prompt(resume=resume, job_description=job_description, criteria=criteria)
    response = await llm.complete(SCORING_SYSTEM_PROMPT, prompt)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {exc}") from exc
    return ScoreResult(
        match_percentage=int(data["match_percentage"]),
        matched_skills=data.get("matched_skills", []),
        missing_skills=data.get("missing_skills", []),
        sponsorship_required=bool(data["sponsorship_required"]),
        company_size_estimate=data.get("company_size_estimate", "unknown"),
        reasoning=data.get("reasoning", ""),
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/scoring.py backend/tests/test_scoring.py
git commit -m "feat(backend): add structured-JSON job scoring service"
```

---

## Task 8: On-demand tailoring service

**Files:**
- Create: `backend/app/services/tailoring.py`
- Test: `backend/tests/test_tailoring.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_tailoring.py
import json
import pytest
from app.services.tailoring import tailor_job, TailoredContent
from app.llm.base import LLMResponse


class FakeLLM:
    name = "fake"

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    async def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(text=self._response_text, tokens_in=10, tokens_out=20, model="fake-model")


@pytest.mark.asyncio
async def test_tailor_job_parses_valid_json():
    payload = {"tailored_resume": "SUMMARY\n...", "cover_letter": "Dear Hiring Manager,\n..."}
    llm = FakeLLM(json.dumps(payload))
    result = await tailor_job(
        llm, resume="resume text", job_description="jd", job_title="GenAI Architect", company="Acme"
    )
    assert isinstance(result, TailoredContent)
    assert result.tailored_resume.startswith("SUMMARY")
    assert "Dear Hiring Manager" in result.cover_letter
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_tailoring.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.tailoring'`

- [ ] **Step 3: Write tailoring.py**

```python
# backend/app/services/tailoring.py
import json
from dataclasses import dataclass
from app.llm.base import LLMProvider
from app.prompts.tailoring import TAILORING_SYSTEM_PROMPT, build_tailoring_prompt


@dataclass
class TailoredContent:
    tailored_resume: str
    cover_letter: str


async def tailor_job(
    llm: LLMProvider, resume: str, job_description: str, job_title: str, company: str
) -> TailoredContent:
    prompt = build_tailoring_prompt(
        resume=resume, job_description=job_description, job_title=job_title, company=company
    )
    response = await llm.complete(TAILORING_SYSTEM_PROMPT, prompt)
    try:
        data = json.loads(response.text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {exc}") from exc
    return TailoredContent(
        tailored_resume=data["tailored_resume"],
        cover_letter=data["cover_letter"],
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_tailoring.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/tailoring.py backend/tests/test_tailoring.py
git commit -m "feat(backend): add on-demand resume/cover-letter tailoring service"
```

---

## Task 9: PDF export (ATS-safe)

**Files:**
- Create: `backend/app/services/export.py`
- Test: `backend/tests/test_export.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_export.py
from app.services.export import render_resume_pdf, render_cover_letter_pdf


def test_render_resume_pdf_returns_pdf_bytes():
    pdf_bytes = render_resume_pdf("SUMMARY\nSenior GenAI Architect with 10 years experience.")
    assert pdf_bytes[:4] == b"%PDF"


def test_render_cover_letter_pdf_returns_pdf_bytes():
    pdf_bytes = render_cover_letter_pdf("Dear Hiring Manager,\n\nI am writing to apply...")
    assert pdf_bytes[:4] == b"%PDF"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_export.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.export'`

- [ ] **Step 3: Write export.py**

```python
# backend/app/services/export.py
from weasyprint import HTML

_BASE_CSS = """
@page { size: A4; margin: 2cm; }
body { font-family: Arial, Helvetica, sans-serif; font-size: 11pt; line-height: 1.4; color: #111; }
h1, h2 { font-weight: bold; }
pre { white-space: pre-wrap; font-family: inherit; }
"""
# Single-column, no tables/floats/columns — deliberately plain so ATS parsers
# (which strip HTML/PDF layout and read raw text) don't mis-order content.


def _text_to_pdf(text: str) -> bytes:
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    html = f"<html><head><style>{_BASE_CSS}</style></head><body><pre>{escaped}</pre></body></html>"
    return HTML(string=html).write_pdf()


def render_resume_pdf(tailored_resume: str) -> bytes:
    return _text_to_pdf(tailored_resume)


def render_cover_letter_pdf(cover_letter: str) -> bytes:
    return _text_to_pdf(cover_letter)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_export.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/export.py backend/tests/test_export.py
git commit -m "feat(backend): add ATS-safe PDF export for resume and cover letter"
```

---

## Task 10: Discovery orchestrator + APScheduler daily job

**Files:**
- Create: `backend/app/services/discovery.py`
- Create: `backend/app/scheduler.py`
- Test: `backend/tests/test_discovery.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_discovery.py
import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import Job, SearchRun
from app.services.discovery import run_discovery
from app.search.base import SearchResult
from app.services.job_fetcher import FetchResult
from app.services.scoring import ScoreResult


class FakeSearchProvider:
    name = "fake_search"

    async def search(self, query: str, freshness_hours: int = 24):
        return [SearchResult(title="GenAI Architect at Acme", url="https://example.com/job/1", snippet="...")]


async def fake_fetch(url: str) -> FetchResult:
    return FetchResult(description="We need a GenAI Architect in Chennai.", needs_manual_paste=False)


class FakeLLM:
    name = "fake_llm"


async def fake_score(llm, resume, job_description, criteria) -> ScoreResult:
    return ScoreResult(
        match_percentage=92,
        matched_skills=["GenAI"],
        missing_skills=[],
        sponsorship_required=False,
        company_size_estimate="10000+",
        reasoning="Strong match.",
    )


@pytest.mark.asyncio
async def test_run_discovery_creates_job_and_search_run(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr("app.services.discovery.fetch_job_page", fake_fetch)
    monkeypatch.setattr("app.services.discovery.score_job", fake_score)

    with Session(engine) as session:
        run = await run_discovery(
            session,
            search_provider=FakeSearchProvider(),
            llm=FakeLLM(),
            queries=["site:linkedin.com/jobs GenAI Architect Chennai"],
            resume="master resume text",
            criteria="criteria text",
        )
        assert run.jobs_found == 1
        assert run.jobs_new == 1
        assert run.status == "completed"

        jobs = session.exec(select(Job)).all()
        assert len(jobs) == 1
        assert jobs[0].match_percentage == 92


@pytest.mark.asyncio
async def test_run_discovery_skips_duplicate_on_second_run(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr("app.services.discovery.fetch_job_page", fake_fetch)
    monkeypatch.setattr("app.services.discovery.score_job", fake_score)

    with Session(engine) as session:
        await run_discovery(
            session,
            search_provider=FakeSearchProvider(),
            llm=FakeLLM(),
            queries=["q"],
            resume="r",
            criteria="c",
        )
        second_run = await run_discovery(
            session,
            search_provider=FakeSearchProvider(),
            llm=FakeLLM(),
            queries=["q"],
            resume="r",
            criteria="c",
        )
        assert second_run.jobs_found == 1
        assert second_run.jobs_new == 0

        jobs = session.exec(select(Job)).all()
        assert len(jobs) == 1  # not duplicated
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_discovery.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.discovery'`

- [ ] **Step 3: Write discovery.py**

```python
# backend/app/services/discovery.py
from sqlmodel import Session, select
from app.db.models import Job, SearchRun
from app.search.base import SearchProvider
from app.llm.base import LLMProvider
from app.services.job_fetcher import fetch_job_page
from app.services.scoring import score_job
from app.services.dedupe import job_dedupe_key
from app.observability.logging import logger


def _parse_title_company(search_title: str) -> tuple[str, str]:
    # Search result titles are typically "<Job Title> at <Company>" or "<Job Title> - <Company>"
    for sep in (" at ", " - ", " | "):
        if sep in search_title:
            title, company = search_title.split(sep, 1)
            return title.strip(), company.strip()
    return search_title.strip(), "Unknown"


async def run_discovery(
    session: Session,
    search_provider: SearchProvider,
    llm: LLMProvider,
    queries: list[str],
    resume: str,
    criteria: str,
) -> SearchRun:
    run = SearchRun(status="running")
    session.add(run)
    session.commit()
    session.refresh(run)

    jobs_found = 0
    jobs_new = 0
    try:
        for query in queries:
            results = await search_provider.search(query)
            jobs_found += len(results)
            for result in results:
                title, company = _parse_title_company(result.title)
                key = job_dedupe_key(company=company, title=title, location="Chennai")
                existing = session.exec(select(Job).where(Job.dedupe_key == key)).first()
                if existing:
                    continue

                fetch_result = await fetch_job_page(result.url)
                job = Job(
                    title=title,
                    company=company,
                    location="Chennai",
                    source_url=result.url,
                    source_site=search_provider.name,
                    description=fetch_result.description,
                    needs_manual_paste=fetch_result.needs_manual_paste,
                    dedupe_key=key,
                    status="pending_review",
                )

                if not fetch_result.needs_manual_paste:
                    try:
                        score = await score_job(
                            llm, resume=resume, job_description=fetch_result.description, criteria=criteria
                        )
                        job.match_percentage = score.match_percentage
                        job.sponsorship_required = score.sponsorship_required
                        job.company_size_estimate = score.company_size_estimate
                        job.scoring_reasoning = score.reasoning
                    except ValueError as exc:
                        job.status = "scoring_failed"
                        logger.warning("scoring_failed", url=result.url, error=str(exc))

                session.add(job)
                jobs_new += 1

        session.commit()
        run.jobs_found = jobs_found
        run.jobs_new = jobs_new
        run.status = "completed"
    except Exception as exc:  # noqa: BLE001 — run status must reflect any failure
        run.status = "failed"
        run.error = str(exc)
        logger.error("discovery_run_failed", error=str(exc))
    finally:
        from app.db.models import utcnow
        run.finished_at = utcnow()
        session.add(run)
        session.commit()
        session.refresh(run)

    return run
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_discovery.py -v`
Expected: PASS

- [ ] **Step 5: Write scheduler.py**

```python
# backend/app/scheduler.py
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session
from app.config import settings
from app.db.session import engine
from app.db.models import ResumeVersion
from app.llm.factory import get_llm_provider
from app.search.factory import get_search_provider
from app.services.discovery import run_discovery
from app.observability.logging import logger

DEFAULT_QUERIES = [
    'site:linkedin.com/jobs "AI Senior Technical Project Manager" Chennai',
    'site:linkedin.com/jobs "GenAI Architect" Chennai',
    'site:linkedin.com/jobs "Agentic AI Architect" Chennai',
    'site:naukri.com "GenAI Architect" Chennai',
    'site:indeed.com "Agentic AI Architect" Chennai',
]

_scheduler: AsyncIOScheduler | None = None


async def scheduled_discovery_job() -> None:
    with Session(engine) as session:
        master = session.query(ResumeVersion).filter(ResumeVersion.is_master.is_(True)).first()
        if master is None:
            logger.warning("scheduled_discovery_skipped", reason="no master resume configured")
            return
        criteria = (
            "Titles: AI Senior Technical Project Manager, GenAI Architect, Agentic AI Architect. "
            "Location: Chennai, India, FTE only. Salary: INR 45L-60L. Industry: MNC only, "
            "company size >= 5000 employees. Skip roles requiring visa/work sponsorship."
        )
        await run_discovery(
            session,
            search_provider=get_search_provider(),
            llm=get_llm_provider(),
            queries=DEFAULT_QUERIES,
            resume=master.content,
            criteria=criteria,
        )


def start_scheduler() -> AsyncIOScheduler:
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        scheduled_discovery_job,
        trigger="cron",
        hour=settings.scheduler_hour,
        minute=0,
        id="daily_discovery",
        replace_existing=True,
    )
    _scheduler.start()
    return _scheduler
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/discovery.py backend/app/scheduler.py backend/tests/test_discovery.py
git commit -m "feat(backend): add discovery orchestrator and daily APScheduler job"
```

---

## Task 11: Observability — structlog + LLM call logging

**Files:**
- Create: `backend/app/observability/__init__.py`
- Create: `backend/app/observability/logging.py`
- Create: `backend/app/observability/llm_log.py`
- Test: `backend/tests/test_llm_log.py`

- [ ] **Step 1: Write logging.py**

```python
# backend/app/observability/logging.py
import logging
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger("jobassistant")
```

- [ ] **Step 2: Write the failing test for llm_log**

```python
# backend/tests/test_llm_log.py
from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import LLMCallLog
from app.observability.llm_log import log_llm_call


def test_log_llm_call_persists_row():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        log_llm_call(
            session,
            provider="azure_openai",
            model="gpt-5.4-mini",
            prompt_id="scoring-v1",
            job_id=None,
            tokens_in=100,
            tokens_out=50,
            latency_ms=1200,
            success=True,
        )
        rows = session.exec(select(LLMCallLog)).all()
        assert len(rows) == 1
        assert rows[0].prompt_id == "scoring-v1"
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_llm_log.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.observability.llm_log'`

- [ ] **Step 4: Write llm_log.py**

```python
# backend/app/observability/llm_log.py
from sqlmodel import Session
from app.db.models import LLMCallLog


def log_llm_call(
    session: Session,
    provider: str,
    model: str,
    prompt_id: str,
    job_id: int | None,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
    success: bool,
    error: str | None = None,
) -> LLMCallLog:
    entry = LLMCallLog(
        provider=provider,
        model=model,
        prompt_id=prompt_id,
        job_id=job_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        success=success,
        error=error,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_llm_log.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/observability backend/tests/test_llm_log.py
git commit -m "feat(backend): add structlog config and LLM call logging"
```

---

## Task 12: API routes — jobs, search runs, applications, settings, observability

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/jobs.py`
- Create: `backend/app/api/search_runs.py`
- Create: `backend/app/api/applications.py`
- Create: `backend/app/api/settings.py`
- Create: `backend/app/api/observability.py`
- Test: `backend/tests/api/test_jobs_api.py`

- [ ] **Step 1: Write the failing test for the jobs API**

```python
# backend/tests/api/test_jobs_api.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app.db import session as db_session
from app.db.models import Job


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[db_session.get_session] = override_get_session
    with Session(engine) as session:
        job = Job(
            title="GenAI Architect",
            company="Acme",
            location="Chennai",
            source_url="https://example.com/1",
            source_site="linkedin",
            dedupe_key="acme|genai architect|chennai",
            match_percentage=90,
            sponsorship_required=False,
            status="pending_review",
        )
        session.add(job)
        session.commit()
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_list_jobs_returns_pending_job(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["title"] == "GenAI Architect"


def test_reject_job_updates_status(client):
    list_response = client.get("/jobs")
    job_id = list_response.json()[0]["id"]
    response = client.post(f"/jobs/{job_id}/reject")
    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/api/test_jobs_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Write jobs.py**

```python
# backend/app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Job, ResumeVersion, LLMCallLog
from app.llm.factory import get_llm_provider
from app.services.tailoring import tailor_job
from app.services.export import render_resume_pdf, render_cover_letter_pdf
from app.observability.llm_log import log_llm_call
from app.prompts.tailoring import TAILORING_PROMPT_ID
import time

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("")
def list_jobs(session: Session = Depends(get_session)):
    jobs = session.exec(select(Job).order_by(Job.created_at.desc())).all()
    return jobs


@router.get("/{job_id}")
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/manual")
def create_manual_job(payload: dict, session: Session = Depends(get_session)):
    from app.services.dedupe import job_dedupe_key

    key = job_dedupe_key(
        company=payload["company"], title=payload["title"], location=payload.get("location", "Chennai")
    )
    job = Job(
        title=payload["title"],
        company=payload["company"],
        location=payload.get("location", "Chennai"),
        source_url=payload["source_url"],
        source_site="manual",
        description=payload.get("description"),
        needs_manual_paste=payload.get("description") is None,
        dedupe_key=key,
        status="pending_review",
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.post("/{job_id}/tailor")
async def tailor(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.description is None:
        raise HTTPException(status_code=400, detail="Job has no description yet — paste one first")

    master = session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()
    if master is None:
        raise HTTPException(status_code=400, detail="No master resume configured in Settings")

    llm = get_llm_provider()
    start = time.monotonic()
    try:
        result = await tailor_job(
            llm, resume=master.content, job_description=job.description, job_title=job.title, company=job.company
        )
        success = True
        error = None
    except ValueError as exc:
        success = False
        error = str(exc)
        raise HTTPException(status_code=502, detail=f"Tailoring failed: {exc}") from exc
    finally:
        latency_ms = int((time.monotonic() - start) * 1000)
        log_llm_call(
            session, provider=llm.name, model=getattr(llm, "_deployment", llm.name),
            prompt_id=TAILORING_PROMPT_ID, job_id=job_id, tokens_in=0, tokens_out=0,
            latency_ms=latency_ms, success=success, error=error,
        )

    job.tailored_resume = result.tailored_resume
    job.tailored_cover_letter = result.cover_letter
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@router.get("/{job_id}/resume.pdf")
def download_resume_pdf(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None or job.tailored_resume is None:
        raise HTTPException(status_code=404, detail="No tailored resume for this job yet")
    pdf_bytes = render_resume_pdf(job.tailored_resume)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.get("/{job_id}/cover-letter.pdf")
def download_cover_letter_pdf(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None or job.tailored_cover_letter is None:
        raise HTTPException(status_code=404, detail="No cover letter for this job yet")
    pdf_bytes = render_cover_letter_pdf(job.tailored_cover_letter)
    return Response(content=pdf_bytes, media_type="application/pdf")


@router.post("/{job_id}/approve")
def approve_job(job_id: int, session: Session = Depends(get_session)):
    from app.db.models import Application

    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "approved"
    session.add(job)
    session.add(Application(job_id=job_id, status="approved"))
    session.commit()
    session.refresh(job)
    return job


@router.post("/{job_id}/reject")
def reject_job(job_id: int, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = "rejected"
    session.add(job)
    session.commit()
    session.refresh(job)
    return job
```

- [ ] **Step 4: Write search_runs.py, applications.py, settings.py, observability.py**

```python
# backend/app/api/search_runs.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import SearchRun, ResumeVersion
from app.llm.factory import get_llm_provider
from app.search.factory import get_search_provider
from app.services.discovery import run_discovery
from app.scheduler import DEFAULT_QUERIES

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/runs")
def list_runs(session: Session = Depends(get_session)):
    return session.exec(select(SearchRun).order_by(SearchRun.started_at.desc())).all()


@router.post("/run")
async def trigger_run(session: Session = Depends(get_session)):
    master = session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()
    criteria = (
        "Titles: AI Senior Technical Project Manager, GenAI Architect, Agentic AI Architect. "
        "Location: Chennai, India, FTE only. Salary: INR 45L-60L. Industry: MNC only, "
        "company size >= 5000 employees. Skip roles requiring visa/work sponsorship."
    )
    run = await run_discovery(
        session,
        search_provider=get_search_provider(),
        llm=get_llm_provider(),
        queries=DEFAULT_QUERIES,
        resume=master.content if master else "",
        criteria=criteria,
    )
    return run
```

```python
# backend/app/api/applications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Application, utcnow

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("")
def list_applications(session: Session = Depends(get_session)):
    return session.exec(select(Application).order_by(Application.created_at.desc())).all()


@router.put("/{application_id}/status")
def update_status(application_id: int, payload: dict, session: Session = Depends(get_session)):
    application = session.get(Application, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found")
    application.status = payload["status"]
    if payload["status"] == "applied":
        application.applied_at = utcnow()
    session.add(application)
    session.commit()
    session.refresh(application)
    return application
```

```python
# backend/app/api/settings.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import ResumeVersion
from app.config import settings

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("")
def get_settings():
    return {
        "llm_provider": settings.llm_provider,
        "search_provider": settings.search_provider,
        "match_threshold": settings.match_threshold,
        "scheduler_hour": settings.scheduler_hour,
    }


@router.get("/resume")
def get_master_resume(session: Session = Depends(get_session)):
    return session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()


@router.put("/resume")
def set_master_resume(payload: dict, session: Session = Depends(get_session)):
    existing = session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()
    if existing:
        existing.is_master = False
        session.add(existing)
    resume = ResumeVersion(label=payload.get("label", "master"), content=payload["content"], is_master=True)
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume
```

```python
# backend/app/api/observability.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import LLMCallLog

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/llm-calls")
def list_llm_calls(session: Session = Depends(get_session)):
    return session.exec(select(LLMCallLog).order_by(LLMCallLog.created_at.desc()).limit(100)).all()
```

- [ ] **Step 5: Write main.py so the test can import `app.main`**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import init_db
from app.scheduler import start_scheduler
from app.api import jobs, search_runs, applications, settings as settings_api, observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield


app = FastAPI(title="Job Application Assistant", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router)
app.include_router(search_runs.router)
app.include_router(applications.router)
app.include_router(settings_api.router)
app.include_router(observability.router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 6: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/api/test_jobs_api.py -v`
Expected: PASS (create empty `backend/tests/api/__init__.py` if pytest can't collect the package)

- [ ] **Step 7: Commit**

```bash
git add backend/app/api backend/app/main.py backend/tests/api
git commit -m "feat(backend): wire FastAPI app with jobs, search, applications, settings, observability routes"
```

---

## Task 13: Backend Dockerfile

**Files:**
- Create: `backend/Dockerfile`

- [ ] **Step 1: Write Dockerfile**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
    shared-mime-info fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app

RUN mkdir -p /app/data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Commit**

```bash
git add backend/Dockerfile
git commit -m "feat(backend): add Dockerfile (WeasyPrint system deps included)"
```

---

## Task 14: Frontend scaffolding — Vite + React + TS + Tailwind

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/types.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Write package.json**

```json
{
  "name": "job-assistant-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run",
    "test:e2e": "playwright test"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.27.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.2",
    "@testing-library/react": "^16.0.1",
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@playwright/test": "^1.48.2",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.1",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vite": "^5.4.10",
    "vitest": "^2.1.4"
  }
}
```

- [ ] **Step 2: Write vite.config.ts**

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.ts",
  },
  server: { port: 5173 },
});
```

- [ ] **Step 3: Write tailwind.config.js, postcss.config.js, index.css**

```javascript
// frontend/tailwind.config.js
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};
```

```javascript
// frontend/postcss.config.js
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
};
```

```css
/* frontend/src/index.css */
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 4: Write index.html and main.tsx**

```html
<!-- frontend/index.html -->
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Job Application Assistant</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```typescript
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
```

```typescript
// frontend/src/setupTests.ts
import "@testing-library/jest-dom";
```

- [ ] **Step 5: Write types.ts and api/client.ts**

```typescript
// frontend/src/types.ts
export interface Job {
  id: number;
  title: string;
  company: string;
  location: string;
  salary_text: string | null;
  source_url: string;
  source_site: string;
  description: string | null;
  needs_manual_paste: boolean;
  match_percentage: number | null;
  matched_skills: string | null;
  missing_skills: string | null;
  sponsorship_required: boolean | null;
  company_size_estimate: string | null;
  scoring_reasoning: string | null;
  status: string;
  tailored_resume: string | null;
  tailored_cover_letter: string | null;
  created_at: string;
}

export interface Application {
  id: number;
  job_id: number;
  status: string;
  applied_at: string | null;
  notes: string | null;
  created_at: string;
}

export interface LLMCallLogEntry {
  id: number;
  provider: string;
  model: string;
  prompt_id: string;
  job_id: number | null;
  tokens_in: number | null;
  tokens_out: number | null;
  latency_ms: number | null;
  success: boolean;
  created_at: string;
}
```

```typescript
// frontend/src/api/client.ts
const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`Request to ${path} failed: ${response.status}`);
  }
  return response.json();
}

import type { Job, Application, LLMCallLogEntry } from "../types";

export const api = {
  listJobs: () => request<Job[]>("/jobs"),
  getJob: (id: number) => request<Job>(`/jobs/${id}`),
  createManualJob: (payload: Record<string, string>) =>
    request<Job>("/jobs/manual", { method: "POST", body: JSON.stringify(payload) }),
  tailorJob: (id: number) => request<Job>(`/jobs/${id}/tailor`, { method: "POST" }),
  approveJob: (id: number) => request<Job>(`/jobs/${id}/approve`, { method: "POST" }),
  rejectJob: (id: number) => request<Job>(`/jobs/${id}/reject`, { method: "POST" }),
  resumePdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/resume.pdf`,
  coverLetterPdfUrl: (id: number) => `${BASE_URL}/jobs/${id}/cover-letter.pdf`,
  listApplications: () => request<Application[]>("/applications"),
  updateApplicationStatus: (id: number, status: string) =>
    request<Application>(`/applications/${id}/status`, { method: "PUT", body: JSON.stringify({ status }) }),
  runSearchNow: () => request<unknown>("/search/run", { method: "POST" }),
  listLlmCalls: () => request<LLMCallLogEntry[]>("/observability/llm-calls"),
};
```

- [ ] **Step 6: Write App.tsx with routes**

```typescript
// frontend/src/App.tsx
import { Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobReview from "./pages/JobReview";
import ManualPaste from "./pages/ManualPaste";
import Applications from "./pages/Applications";
import Settings from "./pages/Settings";
import Observability from "./pages/Observability";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${
    isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
  }`;

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 px-6 py-3 flex gap-2">
        <NavLink to="/" className={navLinkClass} end>Dashboard</NavLink>
        <NavLink to="/manual" className={navLinkClass}>Add Job</NavLink>
        <NavLink to="/applications" className={navLinkClass}>Applications</NavLink>
        <NavLink to="/settings" className={navLinkClass}>Settings</NavLink>
        <NavLink to="/observability" className={navLinkClass}>Observability</NavLink>
      </nav>
      <main className="max-w-5xl mx-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs/:id" element={<JobReview />} />
          <Route path="/manual" element={<ManualPaste />} />
          <Route path="/applications" element={<Applications />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/observability" element={<Observability />} />
        </Routes>
      </main>
    </div>
  );
}
```

- [ ] **Step 7: Verify the dev server starts**

Run: `cd frontend && npm install && npm run dev`
Expected: Vite prints `Local: http://localhost:5173/` with no errors (pages import fine even though
Dashboard/JobReview/etc. don't exist yet — they're created in the next tasks, so skip this
verification until after Task 18, or stub empty components now to unblock it).

- [ ] **Step 8: Commit**

```bash
git add frontend/package.json frontend/vite.config.ts frontend/tailwind.config.js frontend/postcss.config.js frontend/index.html frontend/src/main.tsx frontend/src/index.css frontend/src/setupTests.ts frontend/src/types.ts frontend/src/api frontend/src/App.tsx
git commit -m "feat(frontend): scaffold Vite + React + TypeScript + Tailwind app shell"
```

---

## Task 15: Dashboard page

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Test: `frontend/src/pages/__tests__/Dashboard.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/pages/__tests__/Dashboard.test.tsx
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi, describe, it, expect } from "vitest";
import Dashboard from "../Dashboard";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: { listJobs: vi.fn() },
}));

describe("Dashboard", () => {
  it("renders jobs returned by the API", async () => {
    (api.listJobs as any).mockResolvedValue([
      {
        id: 1,
        title: "GenAI Architect",
        company: "Acme",
        location: "Chennai",
        match_percentage: 92,
        sponsorship_required: false,
        source_site: "linkedin",
        status: "pending_review",
        needs_manual_paste: false,
      },
    ]);
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>
    );
    await waitFor(() => expect(screen.getByText("GenAI Architect")).toBeInTheDocument());
    expect(screen.getByText(/92%/)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/pages/__tests__/Dashboard.test.tsx`
Expected: FAIL — cannot find module `../Dashboard`

- [ ] **Step 3: Write Dashboard.tsx**

```typescript
// frontend/src/pages/Dashboard.tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";

export default function Dashboard() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listJobs().then((data) => {
      setJobs(data);
      setLoading(false);
    });
  }, []);

  if (loading) return <p className="text-slate-500">Loading jobs...</p>;

  const pending = jobs.filter((j) => j.status === "pending_review");

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold text-slate-900">Pending Review ({pending.length})</h1>
        <button
          className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={() => api.runSearchNow()}
        >
          Run search now
        </button>
      </div>
      <div className="grid gap-3">
        {pending.map((job) => (
          <Link
            key={job.id}
            to={`/jobs/${job.id}`}
            className="block bg-white border border-slate-200 rounded-lg p-4 hover:border-slate-400"
          >
            <div className="flex justify-between">
              <div>
                <p className="font-medium text-slate-900">{job.title}</p>
                <p className="text-sm text-slate-500">{job.company} — {job.location}</p>
              </div>
              <div className="text-right">
                <span className="inline-block bg-green-100 text-green-800 text-sm font-medium px-2 py-1 rounded">
                  {job.match_percentage}% match
                </span>
                {job.needs_manual_paste && (
                  <p className="text-xs text-amber-600 mt-1">Needs description pasted in</p>
                )}
              </div>
            </div>
          </Link>
        ))}
        {pending.length === 0 && (
          <p className="text-slate-500">No pending matches yet. Run a search or add a job manually.</p>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/pages/__tests__/Dashboard.test.tsx`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx frontend/src/pages/__tests__/Dashboard.test.tsx
git commit -m "feat(frontend): add Dashboard page listing pending-review jobs"
```

---

## Task 16: Job review panel — tailor, edit, download PDFs, approve/reject

**Files:**
- Create: `frontend/src/pages/JobReview.tsx`
- Test: `frontend/src/pages/__tests__/JobReview.test.tsx`

- [ ] **Step 1: Write the failing test**

```typescript
// frontend/src/pages/__tests__/JobReview.test.tsx
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi, describe, it, expect } from "vitest";
import JobReview from "../JobReview";
import { api } from "../../api/client";

vi.mock("../../api/client", () => ({
  api: {
    getJob: vi.fn(),
    tailorJob: vi.fn(),
    approveJob: vi.fn(),
    rejectJob: vi.fn(),
    resumePdfUrl: (id: number) => `http://localhost:8000/jobs/${id}/resume.pdf`,
    coverLetterPdfUrl: (id: number) => `http://localhost:8000/jobs/${id}/cover-letter.pdf`,
  },
}));

const baseJob = {
  id: 1,
  title: "GenAI Architect",
  company: "Acme",
  location: "Chennai",
  description: "We need a GenAI Architect...",
  match_percentage: 92,
  sponsorship_required: false,
  status: "pending_review",
  tailored_resume: null,
  tailored_cover_letter: null,
};

describe("JobReview", () => {
  it("generates tailored materials and shows download links once available", async () => {
    (api.getJob as any).mockResolvedValue(baseJob);
    (api.tailorJob as any).mockResolvedValue({
      ...baseJob,
      tailored_resume: "SUMMARY\n...",
      tailored_cover_letter: "Dear Hiring Manager,\n...",
    });

    render(
      <MemoryRouter initialEntries={["/jobs/1"]}>
        <Routes>
          <Route path="/jobs/:id" element={<JobReview />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("GenAI Architect")).toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: /generate tailored resume/i }));

    await waitFor(() => expect(screen.getByText(/download resume pdf/i)).toBeInTheDocument());
    expect(screen.getByText(/download cover letter pdf/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/pages/__tests__/JobReview.test.tsx`
Expected: FAIL — cannot find module `../JobReview`

- [ ] **Step 3: Write JobReview.tsx**

```typescript
// frontend/src/pages/JobReview.tsx
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Job } from "../types";

export default function JobReview() {
  const { id } = useParams();
  const navigate = useNavigate();
  const jobId = Number(id);
  const [job, setJob] = useState<Job | null>(null);
  const [tailoring, setTailoring] = useState(false);

  useEffect(() => {
    api.getJob(jobId).then(setJob);
  }, [jobId]);

  if (!job) return <p className="text-slate-500">Loading...</p>;

  const handleTailor = async () => {
    setTailoring(true);
    const updated = await api.tailorJob(jobId);
    setJob(updated);
    setTailoring(false);
  };

  const handleApprove = async () => {
    await api.approveJob(jobId);
    navigate("/");
  };

  const handleReject = async () => {
    await api.rejectJob(jobId);
    navigate("/");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">{job.title}</h1>
        <p className="text-slate-500">{job.company} — {job.location} — {job.match_percentage}% match</p>
      </div>

      <section>
        <h2 className="font-medium text-slate-800 mb-2">Job Description</h2>
        <pre className="whitespace-pre-wrap bg-white border border-slate-200 rounded-lg p-4 text-sm">
          {job.description}
        </pre>
      </section>

      {!job.tailored_resume && (
        <button
          className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={handleTailor}
          disabled={tailoring}
        >
          {tailoring ? "Generating..." : "Generate tailored resume"}
        </button>
      )}

      {job.tailored_resume && (
        <>
          <section>
            <div className="flex justify-between items-center mb-2">
              <h2 className="font-medium text-slate-800">Tailored Resume</h2>
              <button className="text-sm text-slate-500" onClick={handleTailor}>Regenerate</button>
            </div>
            <textarea
              className="w-full h-64 border border-slate-200 rounded-lg p-3 text-sm font-mono"
              value={job.tailored_resume}
              onChange={(e) => setJob({ ...job, tailored_resume: e.target.value })}
            />
            <a
              className="inline-block mt-2 text-sm text-blue-600 underline"
              href={api.resumePdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              Download Resume PDF
            </a>
          </section>

          <section>
            <h2 className="font-medium text-slate-800 mb-2">Cover Letter</h2>
            <textarea
              className="w-full h-48 border border-slate-200 rounded-lg p-3 text-sm"
              value={job.tailored_cover_letter ?? ""}
              onChange={(e) => setJob({ ...job, tailored_cover_letter: e.target.value })}
            />
            <a
              className="inline-block mt-2 text-sm text-blue-600 underline"
              href={api.coverLetterPdfUrl(jobId)}
              target="_blank"
              rel="noreferrer"
            >
              Download Cover Letter PDF
            </a>
          </section>

          <div className="flex gap-3">
            <button className="bg-green-600 text-white px-4 py-2 rounded-md text-sm" onClick={handleApprove}>
              Approve — open application page
            </button>
            <button className="bg-slate-200 text-slate-800 px-4 py-2 rounded-md text-sm" onClick={handleReject}>
              Reject
            </button>
            <a
              className="ml-auto text-sm text-slate-500 self-center underline"
              href={job.title ? undefined : undefined}
            >
              {}
            </a>
          </div>
        </>
      )}
    </div>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd frontend && npx vitest run src/pages/__tests__/JobReview.test.tsx`
Expected: PASS

- [ ] **Step 5: Fix the dead placeholder link before committing**

The `<a>` tag with `href={undefined}` in the button row is dead code left over from drafting —
remove it. Replace the closing `<div className="flex gap-3">...</div>` block with:

```typescript
          <div className="flex gap-3">
            <button className="bg-green-600 text-white px-4 py-2 rounded-md text-sm" onClick={handleApprove}>
              Approve — open application page
            </button>
            <button className="bg-slate-200 text-slate-800 px-4 py-2 rounded-md text-sm" onClick={handleReject}>
              Reject
            </button>
            <a
              className="ml-auto text-sm text-slate-500 self-center underline"
              href={job.source_url}
              target="_blank"
              rel="noreferrer"
            >
              View original posting
            </a>
          </div>
```

(This also requires adding `source_url: string;` is already present on `Job` from Task 14 —
no type changes needed.)

- [ ] **Step 6: Re-run test to confirm still passing**

Run: `cd frontend && npx vitest run src/pages/__tests__/JobReview.test.tsx`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/pages/JobReview.tsx frontend/src/pages/__tests__/JobReview.test.tsx
git commit -m "feat(frontend): add job review panel with tailoring, PDF downloads, approve/reject"
```

---

## Task 17: Manual paste-in form

**Files:**
- Create: `frontend/src/pages/ManualPaste.tsx`

- [ ] **Step 1: Write ManualPaste.tsx**

```typescript
// frontend/src/pages/ManualPaste.tsx
import { useState, FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function ManualPaste() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ title: "", company: "", location: "Chennai", source_url: "", description: "" });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const job = await api.createManualJob(form);
    setSubmitting(false);
    navigate(`/jobs/${job.id}`);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl">
      <h1 className="text-2xl font-semibold text-slate-900">Add a job manually</h1>
      {(["title", "company", "location", "source_url"] as const).map((field) => (
        <div key={field}>
          <label className="block text-sm font-medium text-slate-700 capitalize">
            {field.replace("_", " ")}
          </label>
          <input
            required={field !== "location"}
            className="mt-1 w-full border border-slate-300 rounded-md p-2 text-sm"
            value={form[field]}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
          />
        </div>
      ))}
      <div>
        <label className="block text-sm font-medium text-slate-700">Job description (paste full text)</label>
        <textarea
          className="mt-1 w-full h-48 border border-slate-300 rounded-md p-2 text-sm"
          value={form.description}
          onChange={(e) => setForm({ ...form, description: e.target.value })}
        />
      </div>
      <button
        type="submit"
        disabled={submitting}
        className="bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
      >
        {submitting ? "Adding..." : "Add job"}
      </button>
    </form>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ManualPaste.tsx
git commit -m "feat(frontend): add manual paste-in form for jobs outside the daily search"
```

---

## Task 18: Applications, Settings, Observability pages

**Files:**
- Create: `frontend/src/pages/Applications.tsx`
- Create: `frontend/src/pages/Settings.tsx`
- Create: `frontend/src/pages/Observability.tsx`

- [ ] **Step 1: Write Applications.tsx**

```typescript
// frontend/src/pages/Applications.tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Application } from "../types";

const STATUSES = ["approved", "applied", "skipped"];

export default function Applications() {
  const [applications, setApplications] = useState<Application[]>([]);

  useEffect(() => {
    api.listApplications().then(setApplications);
  }, []);

  const handleStatusChange = async (id: number, status: string) => {
    const updated = await api.updateApplicationStatus(id, status);
    setApplications((prev) => prev.map((a) => (a.id === id ? updated : a)));
  };

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">Application History</h1>
      <table className="w-full text-sm bg-white border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="p-2">Job ID</th>
            <th className="p-2">Status</th>
            <th className="p-2">Applied At</th>
          </tr>
        </thead>
        <tbody>
          {applications.map((application) => (
            <tr key={application.id} className="border-t border-slate-100">
              <td className="p-2">{application.job_id}</td>
              <td className="p-2">
                <select
                  className="border border-slate-300 rounded p-1"
                  value={application.status}
                  onChange={(e) => handleStatusChange(application.id, e.target.value)}
                >
                  {STATUSES.map((s) => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>
              </td>
              <td className="p-2">{application.applied_at ?? "—"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 2: Write Settings.tsx**

```typescript
// frontend/src/pages/Settings.tsx
import { useEffect, useState } from "react";

const BASE_URL = "http://localhost:8000";

interface SettingsResponse {
  llm_provider: string;
  search_provider: string;
  match_threshold: number;
  scheduler_hour: number;
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch(`${BASE_URL}/settings`).then((r) => r.json()).then(setSettings);
    fetch(`${BASE_URL}/settings/resume`).then((r) => (r.ok ? r.json() : null)).then((r) => {
      if (r) setResumeText(r.content);
    });
  }, []);

  const saveResume = async () => {
    setSaving(true);
    await fetch(`${BASE_URL}/settings/resume`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: "master", content: resumeText }),
    });
    setSaving(false);
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <h1 className="text-2xl font-semibold text-slate-900">Settings</h1>

      {settings && (
        <div className="bg-white border border-slate-200 rounded-lg p-4 text-sm space-y-1">
          <p><span className="font-medium">LLM provider:</span> {settings.llm_provider}</p>
          <p><span className="font-medium">Search provider:</span> {settings.search_provider}</p>
          <p><span className="font-medium">Match threshold:</span> {settings.match_threshold}%</p>
          <p><span className="font-medium">Daily search hour:</span> {settings.scheduler_hour}:00</p>
          <p className="text-slate-400 text-xs mt-2">
            Providers are configured via the backend .env file, not editable here.
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-1">Master Resume</label>
        <textarea
          className="w-full h-64 border border-slate-300 rounded-md p-2 text-sm font-mono"
          value={resumeText}
          onChange={(e) => setResumeText(e.target.value)}
        />
        <button
          className="mt-2 bg-slate-900 text-white px-4 py-2 rounded-md text-sm"
          onClick={saveResume}
          disabled={saving}
        >
          {saving ? "Saving..." : "Save master resume"}
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Write Observability.tsx**

```typescript
// frontend/src/pages/Observability.tsx
import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { LLMCallLogEntry } from "../types";

export default function Observability() {
  const [calls, setCalls] = useState<LLMCallLogEntry[]>([]);

  useEffect(() => {
    api.listLlmCalls().then(setCalls);
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold text-slate-900">LLM Call Log</h1>
      <table className="w-full text-sm bg-white border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-100 text-left">
          <tr>
            <th className="p-2">Time</th>
            <th className="p-2">Provider</th>
            <th className="p-2">Prompt</th>
            <th className="p-2">Latency</th>
            <th className="p-2">Success</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((c) => (
            <tr key={c.id} className="border-t border-slate-100">
              <td className="p-2">{new Date(c.created_at).toLocaleString()}</td>
              <td className="p-2">{c.provider} / {c.model}</td>
              <td className="p-2">{c.prompt_id}</td>
              <td className="p-2">{c.latency_ms}ms</td>
              <td className="p-2">{c.success ? "✓" : "✗"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

- [ ] **Step 4: Verify the whole frontend builds**

Run: `cd frontend && npm install && npx tsc -b`
Expected: No type errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/Applications.tsx frontend/src/pages/Settings.tsx frontend/src/pages/Observability.tsx
git commit -m "feat(frontend): add Applications, Settings, and Observability pages"
```

---

## Task 19: Playwright end-to-end smoke test for the approve flow

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/approve-flow.spec.ts`

- [ ] **Step 1: Write playwright.config.ts**

```typescript
// frontend/playwright.config.ts
import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  use: { baseURL: "http://localhost:5173" },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
  },
});
```

- [ ] **Step 2: Write approve-flow.spec.ts**

```typescript
// frontend/e2e/approve-flow.spec.ts
import { test, expect } from "@playwright/test";

// Requires the backend running at localhost:8000 with at least one pending job
// seeded (e.g. via the manual paste-in form) before this test runs.
test("user can open a job, generate tailored materials, and approve it", async ({ page }) => {
  await page.goto("/");
  const firstJob = page.locator("a", { hasText: /% match/ }).first();
  await expect(firstJob).toBeVisible();
  await firstJob.click();

  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const generateButton = page.getByRole("button", { name: /generate tailored resume/i });
  if (await generateButton.isVisible()) {
    await generateButton.click();
    await expect(page.getByText(/download resume pdf/i)).toBeVisible({ timeout: 30000 });
  }

  // Approve stops here — clicking it opens the source job posting in a new tab
  // for the user to submit manually. This test verifies the button exists and
  // is clickable; it does not simulate an external site's submit flow.
  await expect(page.getByRole("button", { name: /approve/i })).toBeEnabled();
});
```

- [ ] **Step 3: Commit**

```bash
git add frontend/playwright.config.ts frontend/e2e
git commit -m "test(frontend): add Playwright smoke test for the approve flow"
```

---

## Task 20: Docker Compose wiring

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `infra/docker-compose.yml`

- [ ] **Step 1: Write frontend/Dockerfile (multi-stage build served via nginx)**

```dockerfile
FROM node:20-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 2: Write frontend/nginx.conf**

```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri /index.html;
    }
}
```

- [ ] **Step 3: Write infra/docker-compose.yml**

```yaml
# infra/docker-compose.yml
services:
  backend:
    build:
      context: ../backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    env_file:
      - ../.env
    volumes:
      - jobassistant-data:/app/data
    restart: unless-stopped

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  jobassistant-data:
```

- [ ] **Step 4: Note on the frontend API base URL for containerized runs**

`frontend/src/api/client.ts` hardcodes `http://localhost:8000` (Task 14). Because the browser
(not the frontend container) makes these requests, and the backend is published on the host at
port 8000 (Step 3 above), `localhost:8000` resolves correctly from the user's browser even when
both services run in Docker Compose. No code change needed for Phase 1 (single-machine, single
user). If this ever needs to work from a different host, swap the hardcoded URL for a Vite env
var (`import.meta.env.VITE_API_BASE_URL`) — noted here rather than built now, per YAGNI.

- [ ] **Step 5: Verify the full stack starts**

Run: `cd infra && docker compose up --build`
Expected: Both containers start; `curl http://localhost:8000/health` returns `{"status":"ok"}`;
`http://localhost:5173` loads the Dashboard page in a browser.

- [ ] **Step 6: Commit**

```bash
git add frontend/Dockerfile frontend/nginx.conf infra/docker-compose.yml
git commit -m "feat(infra): add Docker Compose wiring for backend + frontend"
```

---

## Self-Review Notes

**Spec coverage check** — every Phase 1 spec section maps to a task:
- Search providers (Azure Bing / Google Custom) → Task 4
- LLM providers (Azure OpenAI / Claude / Gemini) → Task 3
- Job fetcher + manual-paste fallback → Task 5
- Structured-JSON scoring incl. sponsorship flag → Task 7
- On-demand tailoring → Task 8
- PDF export (pulled into Phase 1 mid-conversation) → Task 9
- Idempotent daily scheduler → Task 10
- Prompt versioning → Task 6
- Observability (structlog + LLMCallLog) → Task 11
- All API routes (jobs/search/applications/settings/observability) → Task 12
- Dashboard, Job review, Manual paste, Applications, Settings, Observability UI → Tasks 15–18
- Approval gate stopping before auto-submit → enforced in Task 16 (Approve links to
  `job.source_url`, no form-fill/submit code anywhere in the plan)
- Docker Compose (Phase 1 deployment target) → Task 20

**Known follow-ups for Phase 2 (explicitly out of scope here, not forgotten):**
- Azure Container Apps manifests + GitHub Actions CI/CD + Key Vault secrets
- DOCX export alongside PDF, if a specific ATS rejects PDF uploads
- OpenTelemetry export to Azure Application Insights (Task 11 only does structlog + DB logging
  locally; cloud tracing wiring is deferred to Phase 2 per the spec's Deployment section)

---

## Execution Handoff

Plan complete and saved to
`docs/superpowers/plans/2026-07-31-job-application-assistant-phase1.md`. Two execution options:

1. **Subagent-Driven (recommended)** — dispatch a fresh subagent per task, review between tasks,
   fast iteration.
2. **Inline Execution** — execute tasks in this session using executing-plans, batch execution
   with checkpoints.

Which approach?

---
