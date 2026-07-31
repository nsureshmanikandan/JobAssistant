from sqlmodel import Session
from app.db.models import LLMCallLog


def log_llm_call(
    session: Session,
    provider: str,
    model: str,
    prompt_id: str,
    job_id: int | None,
    tokens_in: int,
    tokens_out: int,
    latency_ms: int,
    success: bool,
    error: str | None = None,
) -> LLMCallLog:
    entry = LLMCallLog(
        provider=provider,
        model=model,
        prompt_id=prompt_id,
        job_id=job_id,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_ms=latency_ms,
        success=success,
        error=error,
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    return entry
