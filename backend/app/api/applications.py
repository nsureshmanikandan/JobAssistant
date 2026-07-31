from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import Application, Job, utcnow

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("")
def list_applications(session: Session = Depends(get_session)):
    applications = session.exec(select(Application).order_by(Application.created_at.desc())).all()
    enriched = []
    for application in applications:
        job = session.get(Job, application.job_id)
        enriched.append(
            {
                **application.model_dump(),
                "job_title": job.title if job else None,
                "job_company": job.company if job else None,
                "job_source_url": job.source_url if job else None,
                "has_tailored_resume": bool(job and job.tailored_resume),
                "has_tailored_cover_letter": bool(job and job.tailored_cover_letter),
            }
        )
    return enriched


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
