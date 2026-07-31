from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import Session
from app.config import settings
from app.criteria import build_criteria_text, build_queries, get_or_create_criteria, primary_location
from app.db.session import engine
from app.db.models import ResumeVersion
from app.llm.factory import get_llm_provider
from app.search.factory import get_search_provider
from app.services.discovery import run_discovery
from app.observability.logging import logger

_scheduler: AsyncIOScheduler | None = None


async def scheduled_discovery_job() -> None:
    with Session(engine) as session:
        master = session.query(ResumeVersion).filter(ResumeVersion.is_master.is_(True)).first()
        if master is None:
            logger.warning("scheduled_discovery_skipped", reason="no master resume configured")
            return
        criteria = get_or_create_criteria(session)
        await run_discovery(
            session,
            search_provider=get_search_provider(),
            llm=get_llm_provider(),
            queries=build_queries(criteria),
            resume=master.content,
            criteria=build_criteria_text(criteria),
            freshness_hours=24,
            default_location=primary_location(criteria),
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
