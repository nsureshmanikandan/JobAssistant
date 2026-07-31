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
