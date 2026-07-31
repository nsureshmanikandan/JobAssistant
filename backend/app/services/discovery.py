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
