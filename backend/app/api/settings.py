from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from app.criteria import get_or_create_criteria
from app.db.session import get_session
from app.db.models import ResumeVersion
from app.config import settings
from app.services.resume_parser import parse_resume_file

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


def _save_master_resume(session: Session, label: str, content: str) -> ResumeVersion:
    existing = session.exec(select(ResumeVersion).where(ResumeVersion.is_master.is_(True))).first()
    if existing:
        existing.is_master = False
        session.add(existing)
    resume = ResumeVersion(label=label, content=content, is_master=True)
    session.add(resume)
    session.commit()
    session.refresh(resume)
    return resume


@router.put("/resume")
def set_master_resume(payload: dict, session: Session = Depends(get_session)):
    return _save_master_resume(session, label=payload.get("label", "master"), content=payload["content"])


@router.post("/resume/upload")
async def upload_master_resume(session: Session = Depends(get_session), file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    file_bytes = await file.read()
    try:
        content = parse_resume_file(file.filename, file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not content.strip():
        raise HTTPException(status_code=400, detail="Could not extract any text from that file")
    return _save_master_resume(session, label=file.filename, content=content)


@router.get("/criteria")
def get_criteria(session: Session = Depends(get_session)):
    return get_or_create_criteria(session)


@router.put("/criteria")
def set_criteria(payload: dict, session: Session = Depends(get_session)):
    criteria = get_or_create_criteria(session)
    for field in (
        "titles", "location", "fte_only", "salary_min_lakhs", "salary_max_lakhs",
        "industry", "min_company_size", "exclude_sponsorship",
    ):
        if field in payload:
            setattr(criteria, field, payload[field])
    session.add(criteria)
    session.commit()
    session.refresh(criteria)
    return criteria
