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
