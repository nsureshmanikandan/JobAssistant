from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.db.session import get_session
from app.db.models import LLMCallLog

router = APIRouter(prefix="/observability", tags=["observability"])


@router.get("/llm-calls")
def list_llm_calls(session: Session = Depends(get_session)):
    return session.exec(select(LLMCallLog).order_by(LLMCallLog.created_at.desc()).limit(100)).all()
