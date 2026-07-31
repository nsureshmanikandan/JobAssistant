import pytest
from sqlmodel import SQLModel, create_engine, Session, select
from app.db.models import Job, SearchRun, LLMCallLog
from app.services.discovery import run_discovery
from app.search.base import SearchResult
from app.services.job_fetcher import FetchResult
from app.services.scoring import ScoreResult


class FakeSearchProvider:
    name = "fake_search"

    async def search(self, query: str, freshness_hours: int = 24):
        return [SearchResult(title="GenAI Architect at Acme", url="https://example.com/job/1", snippet="...")]


class ManyResultsSearchProvider:
    name = "many_results"

    async def search(self, query: str, freshness_hours: int = 24):
        return [
            SearchResult(title=f"GenAI Architect at Company{i}", url=f"https://example.com/job/{i}", snippet="...")
            for i in range(25)
        ]


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

        # Scoring calls during discovery must be logged too, not just tailoring.
        llm_calls = session.exec(select(LLMCallLog)).all()
        assert len(llm_calls) == 1
        assert llm_calls[0].prompt_id == "scoring-v1"
        assert llm_calls[0].success is True


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


@pytest.mark.asyncio
async def test_run_discovery_caps_results_per_query(monkeypatch):
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    monkeypatch.setattr("app.services.discovery.fetch_job_page", fake_fetch)
    monkeypatch.setattr("app.services.discovery.score_job", fake_score)

    with Session(engine) as session:
        run = await run_discovery(
            session,
            search_provider=ManyResultsSearchProvider(),
            llm=FakeLLM(),
            queries=["q"],
            resume="r",
            criteria="c",
        )
        # Provider returned 25 results but the default cap is 10 — scoring is one
        # sequential LLM call per job, so processing everything would make a single
        # search run take far too long.
        assert run.jobs_found == 10
        assert run.jobs_new == 10
        jobs = session.exec(select(Job)).all()
        assert len(jobs) == 10
