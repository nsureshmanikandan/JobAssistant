import time
from sqlmodel import Session, select
from app.db.models import Job, SearchRun
from app.search.base import SearchProvider
from app.llm.base import LLMProvider
from app.services.job_fetcher import fetch_job_page
from app.services.scoring import score_job
from app.services.dedupe import job_dedupe_key
from app.observability.logging import logger
from app.observability.llm_log import log_llm_call
from app.prompts.scoring import SCORING_PROMPT_ID


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
    freshness_hours: int = 24,
    default_location: str = "Chennai",
    max_results_per_query: int = 10,
) -> SearchRun:
    run = SearchRun(status="running")
    session.add(run)
    session.commit()
    session.refresh(run)

    jobs_found = 0
    jobs_new = 0
    try:
        for query in queries:
            results = await search_provider.search(query, freshness_hours=freshness_hours)
            # Cap how many results actually get fetched+scored per query — scoring is
            # one sequential LLM call per job (20-60s each for reasoning models), so
            # processing everything a provider returns (up to 150 for the Apify actor)
            # made a single "Run search now" click take 20+ minutes in practice.
            results = results[:max_results_per_query]
            jobs_found += len(results)
            for result in results:
                title, company = _parse_title_company(result.title)
                # default_location is an approximation, not a per-result attribution:
                # search providers don't return structured location metadata, so when
                # criteria spans multiple locations we can't tell which one matched.
                key = job_dedupe_key(company=company, title=title, location=default_location)
                existing = session.exec(select(Job).where(Job.dedupe_key == key)).first()
                if existing:
                    continue

                fetch_result = await fetch_job_page(result.url)
                job = Job(
                    title=title,
                    company=company,
                    location=default_location,
                    source_url=result.url,
                    source_site=search_provider.name,
                    description=fetch_result.description,
                    needs_manual_paste=fetch_result.needs_manual_paste,
                    dedupe_key=key,
                    status="pending_review",
                )

                if not fetch_result.needs_manual_paste:
                    score_start = time.monotonic()
                    try:
                        score = await score_job(
                            llm, resume=resume, job_description=fetch_result.description, criteria=criteria
                        )
                        job.match_percentage = score.match_percentage
                        job.sponsorship_required = score.sponsorship_required
                        job.company_size_estimate = score.company_size_estimate
                        job.scoring_reasoning = score.reasoning
                        log_llm_call(
                            session, provider=llm.name, model=getattr(llm, "_deployment", llm.name),
                            prompt_id=SCORING_PROMPT_ID, job_id=None,
                            tokens_in=0, tokens_out=0,
                            latency_ms=int((time.monotonic() - score_start) * 1000), success=True,
                        )
                    except ValueError as exc:
                        job.status = "scoring_failed"
                        logger.warning("scoring_failed", url=result.url, error=str(exc))
                        log_llm_call(
                            session, provider=llm.name, model=getattr(llm, "_deployment", llm.name),
                            prompt_id=SCORING_PROMPT_ID, job_id=None,
                            tokens_in=0, tokens_out=0,
                            latency_ms=int((time.monotonic() - score_start) * 1000), success=False, error=str(exc),
                        )

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
