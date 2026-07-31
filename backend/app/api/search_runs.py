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
